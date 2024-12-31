from flask import Flask, render_template, request, jsonify
import json
from src.parser import parse_accounts
from src.visualizer import prepare_sankey_data, create_sankey_figure
from src.analysis import analyze_data

app = Flask(__name__)

# Load and parse JSON once at startup
with open("data/org.json", "r") as f:
    accounts = parse_accounts(json.load(f))


@app.route("/")
def home():
    """
    Renders the home page (templates/home.html).
    """
    return render_template("home.html")


@app.route("/analysis")
def analysis():
    """
    Analyzes the data (accounts) and displays metrics on a new Analysis page.
    """
    # Use the same 'accounts' object loaded at startup
    results = analyze_data(accounts)
    metrics = results["metrics"]
    suggestions = results["suggestions"]

    # Render the analysis template with our calculated metrics
    return render_template(
        "analysis.html",
        metrics=metrics,
        suggestions=suggestions
    )


@app.route("/sankey_diagram")
def sankey_diagram():
    """
    Renders the Sankey Diagram page (templates/sankey_diagram.html).
    Provides dropdown options for filtering.
    """
    account_options = sorted(accounts.keys())
    group_options = sorted({group.name for acct in accounts.values() for group in acct.groups.values()})
    permission_set_options = sorted({
        ps.name 
        for acct in accounts.values() 
        for group in acct.groups.values() 
        for ps in group.permission_sets
    })
    policy_options = sorted({
        policy.name
        for acct in accounts.values()
        for group in acct.groups.values()
        for ps in group.permission_sets
        for policy in ps.aws_managed_policies + ps.inline_policies
    })

    return render_template(
        "sankey_diagram.html",
        account_options=account_options,
        group_options=group_options,
        permission_set_options=permission_set_options,
        policy_options=policy_options,
    )


@app.route("/generate", methods=["POST"])
def generate_sankey():
    """
    POST endpoint to generate Sankey data (nodes, links) 
    given a filter in the request body.
    """
    data = request.json
    selected_objects = data.get("objects", {})  # object with accounts/groups/etc.

    # Build Sankey from the (already loaded) accounts + user-selected filters
    nodes, links = prepare_sankey_data(accounts, selected_objects)
    fig = create_sankey_figure(nodes, links)
    return fig.to_json()


if __name__ == "__main__":
    app.run(debug=True)
