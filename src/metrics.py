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


def extrapolated_rbo(l1: list, l2: list, p = 0.9):
    """
    Calculate extrapolated RBO between two ranked lists.
    - l1: First ranked list
    - l2: Second ranked list
    - p: Probability parameter (default 0.9), controls weight of top ranks
    """
    # Get all items up to a given depth
    def set_at_depth(lst, depth):
        ans = set()
        for v in lst[:depth]:
            if isinstance(v, set):
                ans.update(v)
            else:
                ans.add(v)
        return ans
    
    # Calculate agreement (proportion of shared items) at given depth
    def agreement(depth):
        set1 = set_at_depth(l1, depth)
        set2 = set_at_depth(l2, depth)
        len_intersection = len(set1.intersection(set2))
        return 2 * len_intersection / (len(set1) + len(set2))
    
    # Calculate overlap (count of shared items) at given depth
    def overlap(depth):
        return agreement(depth) * min(depth, len(l1), len(l2))
    
    # Main calculation
    S, L = sorted((l1, l2), key = len)
    s, l = len(S), len(L)
    
    x_l = overlap(l)
    x_s = overlap(s)
    
    sum1 = sum(p ** d * agreement(d) for d in range(1, l + 1))
    sum2 = sum(p ** d * x_s * (d - s) / s / d for d in range(s + 1, l + 1))
    
    term1 = (1 - p) / p * (sum1 + sum2)
    term2 = p ** l * ((x_l - x_s) / l + x_s / s)
    
    return term1 + term2