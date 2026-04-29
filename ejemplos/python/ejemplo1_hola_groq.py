
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

response = client.chat.completions.create(
    model="qwen/qwen3-32b",
    messages=[
        {"role": "user", "content": "Hola, ¿cuál es la capital de Chile? Responde en 1 frase."}
    ],
)

texto = response.choices[0].message.content
print("🤖 Respuesta:")
print(f"   {texto}\n")


print("📊 Uso (lo que te cobran):")
print(f"   Tokens input:  {response.usage.prompt_tokens}")
print(f"   Tokens output: {response.usage.completion_tokens}")
print(f"   Total:         {response.usage.total_tokens}")

# Precios Groq qwen/qwen3-32b: $0.29 input / $0.59 output por 1M tokens
costo_input = response.usage.prompt_tokens * 0.29 / 1_000_000
costo_output = response.usage.completion_tokens * 0.59 / 1_000_000
print(f"   Costo:         ${costo_input + costo_output:.6f} USD")
