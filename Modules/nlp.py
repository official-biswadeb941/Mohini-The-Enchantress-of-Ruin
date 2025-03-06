from textblob import TextBlob

def get_intent(text):
    keywords = {
        "screenshot": ["screenshot", "screen", "capture", "snapshot", "printscreen", "screen grab"],
        "camera": ["photo", "picture", "camera", "selfie", "snap", "click", "image", "photograph"],
        "audio": ["audio", "record sound", "mic", "voice", "microphone", "sound clip", "speech"],
        "video": ["video", "record clip", "film", "movie", "footage", "videotape", "camcorder"],
    }
    
    for intent, words in keywords.items():
        if any(word in text for word in words):
            return intent
    return None
