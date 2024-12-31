from typing import List, Dict, Optional


class Policy:
    def __init__(self, name: str, arn: Optional[str] = None, inline: Optional[str] = None):
        self.name = name
        self.arn = arn
        self.inline = inline

    def __repr__(self):
        return f"Policy(name='{self.name}', arn='{self.arn}', inline={self.inline})"


class PermissionSet:
    def __init__(self, name: str, arn: str, aws_managed_policies: List[Policy], inline_policies: List[Policy]):
        self.name = name
        self.arn = arn
        self.aws_managed_policies = aws_managed_policies
        self.inline_policies = inline_policies

    def __repr__(self):
        return f"PermissionSet(name='{self.name}', arn='{self.arn}', aws_managed_policies={self.aws_managed_policies}, inline_policies={self.inline_policies})"


class Group:
    def __init__(self, name: str, permission_sets: List[PermissionSet]):
        self.name = name
        self.permission_sets = permission_sets

    def __repr__(self):
        return f"Group(name='{self.name}', permission_sets={self.permission_sets})"


class Account:
    def __init__(self, account_id, arn , email, name, groups=None):
        self.account_id = account_id
        self.arn = arn
        self.email = email
        self.name = name
        self.groups = groups if groups is not None else {}

    def __repr__(self):
        return f"Account(Id: {self.account_id}, Name: {self.name}, Email: {self.email}, Arn: {self.arn})"
