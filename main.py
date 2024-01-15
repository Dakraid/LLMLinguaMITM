import gzip
import json
import re

import cloudscraper
import httpx
import yaml
from llmlingua import PromptCompressor
from starlette import requests
from starlette.datastructures import MutableHeaders

from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

syncClient = httpx.Client(base_url=config['base_url'])
asyncClient = httpx.AsyncClient(base_url=config['base_url'])
scraper = cloudscraper.create_scraper()


def create_response(orig_request, api_response: requests) -> Response:
    compressed_content = gzip.compress(api_response.content)
    new_header = MutableHeaders(api_response.headers)
    new_header['content-length'] = str(len(compressed_content))
    api_response.headers = new_header
    orig_request.scope.update(headers=api_response.headers.raw)
    return Response(compressed_content,
                    status_code=api_response.status_code,
                    headers=api_response.headers, )


async def _reverse_proxy_get(request: Request):
    rp_resp = scraper.get(config['base_url'] + request.url.path)
    return create_response(request, rp_resp)


async def _reverse_proxy_post(request: Request):
    rp_resp = scraper.post(config['base_url'] + request.url.path, await request.body())
    return create_response(request, rp_resp)


async def _reverse_proxy_completions(request: Request):
    request_body = await request.json()
    llm_lingua = PromptCompressor(config['model_name'], model_config={'revision': config['branch']})

    with open('input.json', 'w') as input_file:
        json.dump(request_body, input_file, indent=4)
        input_file.close()

        if config['split_instruction']:
            pattern = re.compile(config['instruction_regex'], re.MULTILINE)
            match = pattern.search(request_body['prompt'])
            if match:
                start, end = match.span()
                instruction = request_body['prompt'][start:end]
                split_prompts = request_body['prompt'][end:].splitlines()
            else:
                instruction = ''
                split_prompts = request_body['prompt'].splitlines()

            if config['force_context']:
                forced_context_ids = []

                for i, string in enumerate(split_prompts):
                    if re.match(config['force_context'], string):
                        forced_context_ids.append(i)
            else:
                forced_context_ids = None

            compressed_prompt = llm_lingua.compress_prompt(split_prompts,
                                                           instruction=instruction,
                                                           question='',
                                                           ratio=config['ratio'],
                                                           rank_method=config['rank_method'],
                                                           keep_split=config['keep_split'],
                                                           use_sentence_level_filter=config['sentence_level_filter'],
                                                           force_context_ids=forced_context_ids)
        else:
            split_prompts = request_body['prompt'].splitlines()

            if config['force_context']:
                forced_context_ids = []

                for i, string in enumerate(split_prompts):
                    if re.match(config['force_context'], string):
                        forced_context_ids.append(i)
            else:
                forced_context_ids = None

            compressed_prompt = llm_lingua.compress_prompt(split_prompts,
                                                           instruction='',
                                                           question='',
                                                           ratio=config['ratio'],
                                                           rank_method=config['rank_method'],
                                                           keep_split=config['keep_split'],
                                                           use_sentence_level_filter=config['sentence_level_filter'],
                                                           force_context_ids=forced_context_ids)

    with open('compression.json', 'w') as compression_file:
        json.dump(compressed_prompt, compression_file, indent=4)
        compression_file.close()

    request_body['prompt'] = compressed_prompt['compressed_prompt']

    with open('output.json', 'w') as output_file:
        json.dump(request_body, output_file, indent=4)
        output_file.close()

    rp_resp = scraper.post(config['base_url'] + request.url.path, json=request_body)
    return create_response(request, rp_resp)


app = FastAPI()

app.add_route('/v1/completions', _reverse_proxy_completions, ['POST'])
app.add_route('/{path:path}', _reverse_proxy_get, ['GET'])
app.add_route('/{path:path}', _reverse_proxy_post, ['POST'])
