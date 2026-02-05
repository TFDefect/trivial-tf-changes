import re
from typing import List

from pydriller import Commit, ModificationType, ModifiedFile


def has_only_examples_tests_files_changed(paths):
    undesiredFiles = 0
    tfFile = 0
    others = 0
    none = 0
    for path in paths:
        if path is not None:
            # Modify the condition here
            if re.search(r'test|exampl', path) or (not path.endswith('tf')):
                undesiredFiles += 1
            elif path.endswith('tf'):
                tfFile += 1
        else:
            none += 1
    if len(paths) == 0:
        return True
    if tfFile == 0 and (others > 0 or undesiredFiles > 0 or len(paths) == none):
        return True
    return False


def get_changed_files_in_commit(commit: Commit) -> List[str]:
    file_names = []
    try:
        for modified_file in commit.modified_files:

            if modified_file.new_path is not None:
                file_names.append(modified_file.new_path)
            else:
                # print(file_names)
                file_names.append(modified_file.old_path)

        # print(file_names)

        return file_names
    except:
        print(f"skip {commit.hash}")
    return file_names


def skip_newly_added_file_or_removed(mod: ModifiedFile):
    if mod.change_type in [ModificationType.DELETE,
                           ModificationType.COPY,
                           ModificationType.UNKNOWN]:
        return True
    if (mod.deleted_lines == 0 or mod.added_lines == 0) and (mod.change_type == ModificationType.RENAME):
        return True
    return False


def is_undesired_commit(commit: Commit) -> bool:
    if has_only_examples_tests_files_changed(
                                get_changed_files_in_commit(commit)
                                            ):
        return True
    return False


def valid_file(mod: ModifiedFile, file_ext_to_parse):
    ext = mod.filename.split('.')
    if len(ext) < 2 or re.search(r'test|exampl|\b(doc)\b|\b(docs)\b|\b(spec)\b|\b(specs)\b|markdown', mod.new_path) or ext[1] not in file_ext_to_parse:
        return False
    return True


def beSafeFromSpecialCommit(message):
    # message is a string
    # returns a boolean
    filters = ['merg', 'revert']
    # filters = ['merg', 'revert', 'rebas', 'restor']
    # filters = ['spell', 'fmt', 'typo', 'format', 'merg', 'conflict', 'revert', 'rebas', 'restor']
    safe = True
    for word in filters:
        if word in message:
            safe = False
            break
    return safe


def preprocess(msg, nltk, ps, stop_words, simple_preprocess):
    sentences = []
    # commit.msg
    for sentence in nltk.sent_tokenize(msg):
        # split into words
        tokens = nltk.tokenize.word_tokenize(sentence.lower())
        # remove all tokens that are not alphabetic
        tokens = [word.strip() for word in tokens if word.isalpha()]
        sentences.append(stemminglAndlLemmatization(tokens, ps))

    words = remove_stopwords(sentences, stop_words, simple_preprocess)
    if words:
        sentences = words[0]
    sentences = [string for i, string in enumerate(sentences) if string not in sentences[:i]]
    return sentences


# Do lemmatization keeping only Noun, Adj, Verb, Adverb
def stemminglAndlLemmatization(texts, ps):
    texts_out = []
    for sentence in texts:
        stemmedWord = ps.stem(sentence.lower())
        texts_out.append(stemmedWord)
    return texts_out


def remove_stopwords(texts, stop_words, simple_preprocess):
    return [[word for word in simple_preprocess(str(doc)) if word not in stop_words] for doc in texts]


def get_subs_dire_name(fileDirs):
    fileDirs = fileDirs.split("/")
    if len(fileDirs) == 1:
        subsystem = "root"
        directory = "root"
    else:
        subsystem = fileDirs[0]
        directory = "/".join(fileDirs[0:-1])
    file_name = fileDirs[-1]

    return subsystem, directory, file_name
