from transformers import pipeline

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")  

def summarize_news(text):
    result = summarizer(text, max_length=40, min_length=10, do_sample=False)
    return result[0]['summary_text']
