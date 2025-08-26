from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")  


def summarize_news(text):
    result = summarizer(text, max_length=40, min_length=10, do_sample=False)
    return result[0]['summary_text']
