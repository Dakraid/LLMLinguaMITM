import gzip
import cloudscraper
import httpx
import yaml
from llmlingua import PromptCompressor

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
    return Response(gzip.compress(rp_resp.content),
                    status_code=rp_resp.status_code,
                    headers=rp_resp.headers, )


async def _reverse_proxy_post(request: Request):
    rp_resp = scraper.post(config['base_url'] + request.url.path, await request.body())
    return Response(gzip.compress(rp_resp.content),
                    status_code=rp_resp.status_code,
                    headers=rp_resp.headers, )


async def _reverse_proxy_completions(request: Request):
    request_body = await request.json()
    llm_lingua = PromptCompressor(config['model_name'], model_config={'revision': config['branch']}, device_map=config['device'])
    compressed_prompt = llm_lingua.compress_prompt(request_body['prompt'],
                                                   instruction='',
                                                   question='',
                                                   target_token=config['target_token'])
    request_body['prompt'] = compressed_prompt['compressed_prompt']
    rp_resp = scraper.post(config['base_url'] + request.url.path, json=request_body)
    return Response(gzip.compress(rp_resp.content),
                    status_code=rp_resp.status_code,
                    headers=rp_resp.headers, )


app = FastAPI()

app.add_route('/v1/completions', _reverse_proxy_completions, ['POST'])
app.add_route('/{path:path}', _reverse_proxy_get, ['GET'])
app.add_route('/{path:path}', _reverse_proxy_post, ['POST'])
