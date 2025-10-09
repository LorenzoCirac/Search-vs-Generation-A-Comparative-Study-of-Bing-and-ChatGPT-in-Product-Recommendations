import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.optimize import linear_sum_assignment

# -------------------- On Load --------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------- Metrics --------------------

def syntactic_overlap(l1: list, l2: list) -> float:
    """
    Compute the Szymkiewicz–Simpson coefficient (overlap coefficient)
    between two lists.
    """
    s1 = set(l1)
    s2 = set(l2)
    
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    return len(s1 & s2) / min(len(s1), len(s2))


def semantic_overlap(l1: list, l2: list, threshold: float = 0.85) -> float:
    """
    Compute semantic overlap between two lists of strings by:
      1) encoding with SentenceTransformer,
      2) cosine similarity matrix,
      3) Hungarian assignment to maximize total similarity,
      4) fraction of assigned pairs whose similarity >= threshold,
         normalized by the size of the smaller list.
    """
    # deduplicate
    l1 = list(dict.fromkeys(l1))
    l2 = list(dict.fromkeys(l2))
    
    if not l1 and not l2:
        return 1.0
    if not l1 or not l2:
        return 0.0
    # if model is None:
    #     model = SentenceTransformer("all-MiniLM-L6-v2")

    # embeddings
    emb1 = model.encode(l1)
    emb2 = model.encode(l2)

    # cosine similarity matrix
    similarity_matrix = cosine_similarity(emb1, emb2)

    # hungarian method
    cost_matrix = 1 - similarity_matrix
    row_idx, col_idx = linear_sum_assignment(cost_matrix)
    matches = sum(similarity_matrix[i, j] >= threshold for i, j in zip(row_idx, col_idx))
    
    return matches / min(len(l1), len(l2))