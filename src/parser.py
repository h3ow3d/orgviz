from .classes import Account, Group, PermissionSet, Policy


def parse_policies(policies_data: dict) -> (list, list):
    aws_managed_policies = [
        Policy(name=policy["Name"], arn=policy.get("Arn"))
        for policy in policies_data.get("AWSManaged", [])
    ]
    inline_policies = [
        Policy(name=name, inline=content)
        for name, content in policies_data.get("Inline", {}).items()
    ]
    return aws_managed_policies, inline_policies


def parse_permission_sets(permission_sets_data: list) -> list:
    return [
        PermissionSet(
            name=ps["Name"],
            arn=ps["Arn"],
            aws_managed_policies=parse_policies(ps["Policies"])[0],
            inline_policies=parse_policies(ps["Policies"])[1],
        )
        for ps in permission_sets_data
    ]


def parse_groups(groups_data: dict) -> dict:
    return {
        group_name: Group(
            name=group_name,
            permission_sets=parse_permission_sets(group_data["PermissionSets"]),
        )
        for group_name, group_data in groups_data.items()
    }


def parse_accounts(data: dict) -> dict:
    return {
        account_data["Name"]: Account(
            account_id=account_data["Id"],
            arn=account_data["Arn"],
            email=account_data.get("Email", ""),
            name=account_data["Name"],
            groups=parse_groups(account_data["Groups"]),
        )
        for account_data in data.values()
    }
