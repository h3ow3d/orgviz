from collections import defaultdict
from typing import Dict, Any

def analyze_data(accounts: Dict[str, Any], similarity_threshold: float = 0.6) -> Dict[str, Any]:
    """
    Analyzes the aggregated data (accounts -> groups -> permission sets -> policies)
    and returns a dictionary of useful metrics and suggestions, including:
      - Permission sets with high policy overlap (Jaccard similarity >= threshold).
      - Rarely used policies, plus details about which account(s) and group(s) they're assigned to.

    :param accounts: Dict of account objects from parse_accounts().
    :param similarity_threshold: Cutoff for highlighting similar permission sets (default=0.6).
    :return: Dictionary containing 'metrics' and 'suggestions'.
    """

    total_accounts = len(accounts)
    total_groups = 0
    total_permission_sets = 0
    total_policies_assigned = 0

    # For permission set similarity
    # Map: ps_name -> set_of_policy_names
    ps_policy_map = {}

    # For policy usage and location details
    policy_usage_count = defaultdict(int)
    policy_usage_locations = defaultdict(set)

    # -------------------
    # 1. Gather Stats
    # -------------------
    for account_name, account in accounts.items():
        total_groups += len(account.groups)

        for group_name, group in account.groups.items():
            for ps in group.permission_sets:
                total_permission_sets += 1

                ps_policy_names = []

                # AWS-managed
                for pol in ps.aws_managed_policies:
                    ps_policy_names.append(pol.name)
                    policy_usage_count[pol.name] += 1
                    policy_usage_locations[pol.name].add((account.account_id, group.name))

                # Inline
                for pol in ps.inline_policies:
                    ps_policy_names.append(pol.name)
                    policy_usage_count[pol.name] += 1
                    policy_usage_locations[pol.name].add((account.account_id, group.name))

                # Store the set in ps_policy_map
                ps_policy_map.setdefault(ps.name, set()).update(ps_policy_names)

                # For total assigned policies
                total_policies_assigned += len(ps_policy_names)

    # -------------------
    # 2. Jaccard Similarity for Permission Sets
    # -------------------
    ps_names = list(ps_policy_map.keys())
    similar_ps_pairs = []

    for i in range(len(ps_names)):
        for j in range(i + 1, len(ps_names)):
            psA = ps_names[i]
            psB = ps_names[j]

            setA = ps_policy_map[psA]
            setB = ps_policy_map[psB]

            # Compute union, intersection
            if not setA and not setB:
                similarity = 1.0
                intersection = set()
            else:
                union = setA.union(setB)
                intersection = setA.intersection(setB)
                similarity = len(intersection) / len(union) if union else 0.0

            # If meets threshold, build a 4-item tuple
            if similarity >= similarity_threshold:
                overlap_list = sorted(intersection)  # e.g. list of shared policy names
                similar_ps_pairs.append((psA, psB, round(similarity, 2), overlap_list))

    # -------------------
    # 3. Rarely Used Policies (count == 1)
    # -------------------
    rarely_used_policy_details = {}
    for policy_name, count in policy_usage_count.items():
        if count == 1:
            locations = list(policy_usage_locations[policy_name])
            rarely_used_policy_details[policy_name] = locations

    # -------------------
    # 4. Compile Metrics & Suggestions
    # -------------------
    metrics = {
        "total_accounts": total_accounts,
        "total_groups": total_groups,
        "total_permission_sets": len(ps_policy_map),  # Unique named PS
        "total_policies_assigned": total_policies_assigned,
        "similar_ps_pairs": similar_ps_pairs,         # Now 4 items each
        "rarely_used_policy_details": rarely_used_policy_details,
    }

    suggestions = []
    if similar_ps_pairs:
        suggestions.append(
            f"Some permission sets share >= {int(similarity_threshold * 100)}% policy overlap."
        )
    if rarely_used_policy_details:
        policy_list = list(rarely_used_policy_details.keys())
        suggestions.append(f"Policies only used once: {policy_list}")

    return {
        "metrics": metrics,
        "suggestions": suggestions,
    }
