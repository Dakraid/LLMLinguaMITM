import gzip
import json
import zlib

import cloudscraper
import httpx
import yaml
from llmlingua import PromptCompressor
from starlette.datastructures import MutableHeaders

from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

syncClient = httpx.Client(base_url=config['base_url'])
asyncClient = httpx.AsyncClient(base_url=config['base_url'])
scraper = cloudscraper.create_scraper()


async def _reverse_proxy_get(request: Request):
    rp_resp = scraper.get(config['base_url'] + request.url.path)
    compressed_content = gzip.compress(rp_resp.content)
    new_header = MutableHeaders(rp_resp.headers)
    new_header['content-length'] = str(len(compressed_content))
    rp_resp.headers = new_header
    request.scope.update(headers=request.headers.raw)
    return Response(compressed_content,
                    status_code=rp_resp.status_code,
                    headers=rp_resp.headers, )


async def _reverse_proxy_post(request: Request):
    rp_resp = scraper.post(config['base_url'] + request.url.path, await request.body())
    compressed_content = gzip.compress(rp_resp.content)
    new_header = MutableHeaders(rp_resp.headers)
    new_header['content-length'] = str(len(compressed_content))
    rp_resp.headers = new_header
    request.scope.update(headers=request.headers.raw)
    return Response(compressed_content,
                    status_code=rp_resp.status_code,
                    headers=rp_resp.headers, )


async def _reverse_proxy_completions(request: Request):
    request_body = await request.json()
    llm_lingua = PromptCompressor(config['model_name'], model_config={'revision': config['branch']})

    with open('input.json', 'w') as input_file:
        json.dump(request_body, input_file, indent=4)
        input_file.close()

    split_prompts = request_body['prompt'].splitlines()

    compressed_prompt = llm_lingua.compress_prompt(split_prompts,
                                                   instruction='',
                                                   question='',
                                                   ratio=config['ratio'],
                                                   rank_method=config['rank_method'],
                                                   keep_split=config['keep_split'])

    with open('compression.json', 'w') as compression_file:
        json.dump(compressed_prompt, compression_file, indent=4)
        compression_file.close()

    request_body['prompt'] = compressed_prompt['compressed_prompt']

    with open('output.json', 'w') as output_file:
        json.dump(request_body, output_file, indent=4)
        output_file.close()

    rp_resp = scraper.post(config['base_url'] + request.url.path, json=request_body)
    compressed_content = gzip.compress(rp_resp.content)
    new_header = MutableHeaders(rp_resp.headers)
    new_header['content-length'] = str(len(compressed_content))
    rp_resp.headers = new_header
    request.scope.update(headers=request.headers.raw)
    return Response(compressed_content,
                    status_code=rp_resp.status_code,
                    headers=rp_resp.headers, )


app = FastAPI()

app.add_route('/v1/completions', _reverse_proxy_completions, ['POST'])
app.add_route('/{path:path}', _reverse_proxy_get, ['GET'])
app.add_route('/{path:path}', _reverse_proxy_post, ['POST'])
