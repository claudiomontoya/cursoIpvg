
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4.1-nano",
    messages=[
        {"role":"system","content":"Eres un experto en capitales del mundo y solo debes responder a preguntas sobre capitales, el resto indicar quee sta fuera del ambito."},
        {"role": "user", "content": "me puedesdar una receta con pollo y papas"},
        {"role": "assistant", "content": "Lo siento, eso está fuera de mi ámbito. Solo respondo preguntas sobre capitales del mundo."},
        {"role":"user", "content": "ok, dame la de alemania"}
    ],
)

texto = response.choices[0].message.content
print("🤖 Respuesta:")
print(f"   {texto}\n")


print("📊 Uso (lo que te cobran):")
print(f"   Tokens input:  {response.usage.prompt_tokens}")
print(f"   Tokens output: {response.usage.completion_tokens}")
print(f"   Total:         {response.usage.total_tokens}")

# 6. Ver cuánto costó aproximadamente (gpt-4o-mini: $0.15 input / $0.60 output por 1M tokens)
costo_input = response.usage.prompt_tokens * 0.15 / 1_000_000
costo_output = response.usage.completion_tokens * 0.60 / 1_000_000
print(f"   Costo:         ${costo_input + costo_output:.6f} USD")

