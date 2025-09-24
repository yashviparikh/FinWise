from transformers import pipeline

try:
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", framework="pt")  
except Exception as e:
    print("⚠️ Summarizer failed, falling back to simple truncation:", e)
    summarizer = None

def summarize_news(text):
    if summarizer:
        result = summarizer(text, max_length=40, min_length=10, do_sample=False)
        return result[0]['summary_text']
    return text[:100] + "..."
