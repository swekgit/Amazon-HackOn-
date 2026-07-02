import json, boto3

b = boto3.client("bedrock-runtime", region_name="us-east-1")
r = b.invoke_model(
    modelId="cohere.embed-multilingual-v3",
    body=json.dumps({"texts": ["gajar ka halwa"], "input_type": "search_query"}),
)
vec = json.loads(r["body"].read())["embeddings"][0]
print("OK, dimension =", len(vec))   # -> OK, dimension = 1024