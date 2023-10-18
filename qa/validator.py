# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import nltk
from nltk.corpus import wordnet


def are_strings_semantically_same(string1, string2):
    # Tokenize the strings into words
    tokens1 = nltk.word_tokenize(string1)
    tokens2 = nltk.word_tokenize(string2)

    # Perform POS tagging
    pos1 = nltk.pos_tag(tokens1)
    pos2 = nltk.pos_tag(tokens2)

    # Lemmatize the words using WordNet
    lemmatizer = nltk.WordNetLemmatizer()
    lemmas1 = [
        lemmatizer.lemmatize(token[0].lower(), get_wordnet_pos(token[1]))
        for token in pos1
    ]
    lemmas2 = [
        lemmatizer.lemmatize(token[0].lower(), get_wordnet_pos(token[1]))
        for token in pos2
    ]

    # Calculate semantic similarity using Wu-Palmer Similarity
    similarity = semantic_similarity(lemmas1, lemmas2)

    # Determine if the similarity exceeds a threshold (e.g., 0.8)
    if similarity >= 0.8:
        return True
    else:
        return False


def get_wordnet_pos(tag):
    """Map POS tags to WordNet POS tags"""
    if tag.startswith("J"):
        return wordnet.ADJ
    elif tag.startswith("V"):
        return wordnet.VERB
    elif tag.startswith("N"):
        return wordnet.NOUN
    elif tag.startswith("R"):
        return wordnet.ADV
    else:
        return wordnet.NOUN  # default to noun


def semantic_similarity(words1, words2):
    """Calculate the maximum Wu-Palmer Similarity between any pair of words"""
    max_similarity = 0.0
    for word1 in words1:
        for word2 in words2:
            synsets1 = wordnet.synsets(word1)
            synsets2 = wordnet.synsets(word2)
            for synset1 in synsets1:
                for synset2 in synsets2:
                    similarity = synset1.wup_similarity(synset2)
                    if similarity is not None and similarity > max_similarity:
                        max_similarity = similarity
    return max_similarity


if __name__ == "__main__":
    # Example usage
    string1 = "Hello, how are you doing?"
    string2 = "Hi, how are you?"
    # string2 = "Goodbye, see you next time!"
    if are_strings_semantically_same(string1, string2):
        print("The strings are semantically the same.")
    else:
        print("The strings are not semantically the same.")
