from google.cloud import language_v1

class GNlp:
    def analyze_feeling(self, text):
        client = language_v1.LanguageServiceClient()

        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

        sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment

        return sentiment.score, sentiment.magnitude