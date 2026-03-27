summarizer = None
_summarizer_load_attempted = False


def _get_summarizer():
    global summarizer, _summarizer_load_attempted

    if _summarizer_load_attempted:
        return summarizer

    _summarizer_load_attempted = True

    try:
        from transformers import pipeline

        for task_name in ("summarization", "text2text-generation"):
            try:
                summarizer = pipeline(
                    task_name,
                    model="sshleifer/distilbart-cnn-12-6",
                )
                break
            except Exception:
                summarizer = None

        if summarizer is None:
            raise RuntimeError("No compatible summarization pipeline task found.")
    except Exception as e:
        print("Summarizer unavailable, using text truncation fallback:", e)
        summarizer = None

    return summarizer


def summarize_news(text):
    model = _get_summarizer()
    if model:
        result = model(text, max_length=40, min_length=10, do_sample=False)
        return result[0]["summary_text"]
    return text[:100] + "..."
