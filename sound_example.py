import base64
from openai import OpenAI
from credentials import ChatGPT_TOKEN

client = OpenAI(api_key=ChatGPT_TOKEN)

completion = client.chat.completions.create(
    model="gpt-audio-1.5",
    modalities=["text", "audio"],
    audio={"voice": "alloy", "format": "mp3"},
    messages=[
        {
            "role": "user",
            "content": "Привіт,як справи?"
        }
    ]
)

print(completion.choices[0])

wav_bytes = base64.b64decode(completion.choices[0].message.audio.data)
with open("response.mp3", "wb") as f:
    f.write(wav_bytes)