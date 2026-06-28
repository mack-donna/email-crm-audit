"""Flask CLI command to seed plan data.

Usage:
    flask seed-plans

Run once after the first migration on a fresh database.
Re-running is safe — it skips plans that already exist.
"""
import click
from flask.cli import with_appcontext
from models import db, Plan

PLANS = [
    {
        "name": "starter",
        "display_name": "Starter",
        "price_monthly_cents": 4900,        # $49/mo
        "price_annual_cents": 47040,        # $3,920/yr  ($326/mo — 20% off)
        "max_contacts_per_campaign": 250,
        "max_campaigns_per_month": 3,
        "gmail_accounts_limit": 1,
        "linkedin_enabled": False,
        "research_depth": 1,
        "history_days": 30,
        "team_seats": 1,
        "api_access": False,
        "custom_prompts": False,
    },
    {
        "name": "growth",
        "display_name": "Growth",
        "price_monthly_cents": 14900,       # $149/mo
        "price_annual_cents": 143040,       # $11,920/yr ($993/mo — 20% off)
        "max_contacts_per_campaign": 1000,
        "max_campaigns_per_month": 20,
        "gmail_accounts_limit": 3,
        "linkedin_enabled": True,
        "research_depth": 3,
        "history_days": 365,
        "team_seats": 1,
        "api_access": False,
        "custom_prompts": False,
    },
    {
        "name": "scale",
        "display_name": "Scale",
        "price_monthly_cents": 39900,       # $399/mo
        "price_annual_cents": 383040,       # $31,920/yr ($2,660/mo — 20% off)
        "max_contacts_per_campaign": -1,    # unlimited
        "max_campaigns_per_month": -1,      # unlimited
        "gmail_accounts_limit": 10,
        "linkedin_enabled": True,
        "research_depth": -1,               # all sources
        "history_days": -1,                 # unlimited
        "team_seats": 3,
        "api_access": True,
        "custom_prompts": True,
    },
]


@click.command("seed-plans")
@with_appcontext
def seed_plans_command():
    """Seed the plans table with Starter / Growth / Scale tiers."""
    created = 0
    for data in PLANS:
        existing = Plan.query.filter_by(name=data["name"]).first()
        if existing:
            click.echo(f"  skip  {data['name']} (already exists)")
            continue
        plan = Plan(**data)
        db.session.add(plan)
        created += 1
        click.echo(f"  create {data['name']}")

    db.session.commit()
    click.echo(f"Done — {created} plan(s) created.")
