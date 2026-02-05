from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jellyfish


class Distance:

    def __init__(self, change1: str, change2: str):
        self.change1 = change1
        self.change2 = change2

    def measure_cosine_similarity(self):
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([self.change1, self.change2])
        cosine_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])
        return cosine_sim[0][0]

    def measure_levenshtein_distance(self):
        return jellyfish.levenshtein_distance(self.change1, self.change2)

    def measure_jaro_distance(self):
        return jellyfish.jaro_similarity(self.change1, self.change2)

    def measure_jaro_winkler_similarity(self):
        return jellyfish.jaro_winkler_similarity(self.change1, self.change2)

    def measure_damerau_levenshtein_distance(self):
        return jellyfish.damerau_levenshtein_distance(self.change1, self.change2)

    def measure_hamming_distance(self):
        return jellyfish.hamming_distance(self.change1, self.change2)

    def ratcliff_obershelp_similarity(self):
        similarity = SequenceMatcher(None, self.change1, self.change2).ratio()
        return similarity
