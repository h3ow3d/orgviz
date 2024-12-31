from .classes import Account, Group, PermissionSet, Policy
import plotly.graph_objects as go

def prepare_sankey_data(accounts: dict, selected_filters: dict = None):
    """
    Build nodes and links for a Sankey diagram with strict top-down filtering.
    
    If 'accounts', 'groups', 'permission_sets', or 'policies' are non-empty lists,
    ONLY the matching entities (and their connected sub-entities) will appear.
    """
    if not selected_filters:
        selected_filters = {}

    selected_accounts = selected_filters.get("accounts", [])
    selected_groups = selected_filters.get("groups", [])
    selected_permission_sets = selected_filters.get("permission_sets", [])
    selected_policies = selected_filters.get("policies", [])

    # 1) Build a "filtered" data structure containing only relevant accounts/groups/PS/policies
    filtered_accounts = {}

    for account_name, account in accounts.items():
        # If user selected specific accounts, skip if not in that list
        if selected_accounts and account_name not in selected_accounts:
            continue

        # We'll collect only those groups that match the group filter
        # AND have relevant permission sets/policies
        filtered_groups = {}

        for group_name, group in account.groups.items():
            # If user selected specific groups, skip if not in that list
            if selected_groups and group_name not in selected_groups:
                continue

            # Filter the group's PermissionSets
            filtered_permission_sets = []
            for ps in group.permission_sets:
                # If user selected specific permission sets, skip if not in that list
                if selected_permission_sets and ps.name not in selected_permission_sets:
                    continue

                # Filter policies if user specified them
                all_policies = ps.aws_managed_policies + ps.inline_policies
                relevant_policies = []
                for pol in all_policies:
                    # If user selected specific policies, skip if not in that list
                    if selected_policies and pol.name not in selected_policies:
                        continue
                    relevant_policies.append(pol)

                # If user is filtering by policies, we keep the PS only if it has at least one relevant policy.
                # If there's no policy filter, we keep the PS as is.
                if relevant_policies or not selected_policies:
                    # Make a shallow copy of the PermissionSet with only relevant policies
                    # so we don't mutate the original data.
                    filtered_ps = PermissionSet(
                        name=ps.name,
                        arn=ps.arn,
                        aws_managed_policies=[p for p in relevant_policies if p.inline is None],
                        inline_policies=[p for p in relevant_policies if p.inline is not None],
                    )
                    filtered_permission_sets.append(filtered_ps)

            # Keep the group only if it has at least one relevant PS
            # (i.e. it’s truly connected to the filter)
            if filtered_permission_sets:
                filtered_groups[group_name] = Group(
                    name=group_name,
                    permission_sets=filtered_permission_sets,
                )

        # Keep the account only if it has at least one relevant group
        if filtered_groups:
            filtered_acc = Account(
                account_id=account.account_id,
                arn=account.arn,
                email=account.email,
                name=account.name,
                groups=filtered_groups,
            )
            filtered_accounts[account_name] = filtered_acc

    # 2) Now build the Sankey from ONLY the filtered data
    node_ids = {}
    labels = []
    links = {"source": [], "target": [], "value": []}

    def get_node_id(entity_type, entity_name):
        key = (entity_type, entity_name)
        if key not in node_ids:
            node_ids[key] = len(labels)
            labels.append(entity_name)
        return node_ids[key]

    for account_name, account in filtered_accounts.items():
        account_idx = get_node_id("Account", account_name)

        for group_name, group in account.groups.items():
            group_idx = get_node_id("Group", group_name)
            links["source"].append(account_idx)
            links["target"].append(group_idx)
            links["value"].append(1)

            for ps in group.permission_sets:
                ps_idx = get_node_id("PermissionSet", ps.name)
                links["source"].append(group_idx)
                links["target"].append(ps_idx)
                links["value"].append(1)

                for policy in ps.aws_managed_policies + ps.inline_policies:
                    policy_idx = get_node_id("Policy", policy.name)
                    links["source"].append(ps_idx)
                    links["target"].append(policy_idx)
                    links["value"].append(1)

    return labels, links


def create_sankey_figure(labels: list, links: dict):
    fig = go.Figure(
        go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels
            ),
            link=dict(
                source=links["source"],
                target=links["target"],
                value=links["value"]
            )
        )
    )
    fig.update_layout(title_text="Organization Diagram", font_size=10)
    return fig
