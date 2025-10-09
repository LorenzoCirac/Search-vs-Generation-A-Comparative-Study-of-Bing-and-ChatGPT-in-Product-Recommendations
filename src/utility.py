from collections import Counter
from sentence_transformers import SentenceTransformer, util
import torch

# -------------------- On Load --------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------- Function --------------------

def top_n_semantic_products(list_of_product_lists: list[list[str]], top_n: int = 10, threshold: float = 0.85, return_list: bool = True):
    """
    Get top-N products by semantic similarity and frequency across lists.
    """
    # Get unique items while preserving order
    seen, items = set(), []
    for lst in list_of_product_lists:
        for p in lst:
            if p not in seen:
                seen.add(p)
                items.append(p)
    
    if not items:
        return []
    
    # Count occurrences
    counts = Counter(p for lst in list_of_product_lists for p in lst)
    
    # Encode all items
    with torch.no_grad():
        embeddings = model.encode(items, normalize_embeddings=True, convert_to_tensor=True)
    
    # Group similar items using better clustering
    assigned = [False] * len(items)
    groups = []
    
    for i in range(len(items)):
        if assigned[i]:
            continue
        
        group = [i]
        assigned[i] = True
        
        # Find all similar items to any item in the group
        for j in range(i + 1, len(items)):
            if not assigned[j]:
                # Check similarity to all items in group, use max
                max_sim = max(float(util.cos_sim(embeddings[j], embeddings[idx])) for idx in group)
                if max_sim >= threshold:
                    group.append(j)
                    assigned[j] = True
        
        groups.append(group)
    
    # Pick best representative from each group
    results = []
    for group in groups:
        # Use item that is most similar to others in group (centroid-like)
        best_idx = max(group, key=lambda idx: sum(float(util.cos_sim(embeddings[idx], embeddings[jdx])) for jdx in group))
        count = sum(counts[items[idx]] for idx in group)
        results.append((items[best_idx], count))
    
    # Sort by frequency
    results.sort(key=lambda x: -x[1])
    
    # Return top N
    top_results = results[:top_n] if top_n else results
    if return_list:
        return [name for name, _ in top_results]
    return [(name, count) for name, count in top_results]