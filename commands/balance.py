"""Balance commands for Opinion CLI."""

import click
from typing import Dict, Any
from commands.base import BaseCommand
from display import JSONDisplayer, BalanceDisplayer


class BalanceParser:
    """Parser for balance response data."""

    @staticmethod
    def parse_balance_response(response) -> Dict[str, Any]:
        """Parse balance response into a standardized format."""
        parsed = {
            "errno": getattr(response, "errno", None),
            "errmsg": getattr(response, "errmsg", None),
            "result": None,
        }

        if hasattr(response, "result") and response.result:
            result = response.result
            if hasattr(result, "balances") and result.balances:
                balances = []
                for balance in result.balances:
                    balances.append(
                        {
                            "quote_token": getattr(balance, "quote_token", ""),
                            "available_balance": getattr(
                                balance, "available_balance", "0"
                            ),
                            "frozen_balance": getattr(balance, "frozen_balance", "0"),
                            "total_balance": getattr(balance, "total_balance", "0"),
                            "token_decimals": getattr(balance, "token_decimals", 18),
                        }
                    )

                parsed["result"] = {
                    "balances": balances,
                    "chain_id": getattr(result, "chain_id", ""),
                    "multi_sign_address": getattr(result, "multi_sign_address", ""),
                    "wallet_address": getattr(result, "wallet_address", ""),
                }

        return parsed


@click.command()
@click.option("--json", "-j", is_flag=True, help="Output balance data in JSON format")
def balance(json: bool):
    """Show user's token balances.

    Requires: API_KEY and PRIVATE_KEY environment variables.
    """
    # Validate required credentials first
    if not BaseCommand.validate_balance_requirements():
        return

    try:
        client = BaseCommand.get_client()
        response = client.get_balances()
        parsed_data = BalanceParser.parse_balance_response(response)

        if json:
            click.echo(JSONDisplayer.to_json_string(parsed_data))
            return

        # Handle table format
        if parsed_data["errno"] == 0:
            if parsed_data["result"] and parsed_data["result"]["balances"]:
                balances = parsed_data["result"]["balances"]
                wallet_info = {
                    "wallet_address": parsed_data["result"]["wallet_address"],
                    "chain_id": parsed_data["result"]["chain_id"],
                    "multi_sign_address": parsed_data["result"]["multi_sign_address"],
                }

                formatted_output = BalanceDisplayer.format_balance_table(
                    balances, wallet_info
                )
                click.echo(formatted_output)
            else:
                click.echo("📊 No balances found")
        else:
            error_msg = parsed_data["errmsg"] or "Unknown error"
            errno = parsed_data["errno"] or "Unknown"
            click.echo(
                f"❌ Failed to get balances (errno: {errno}): {error_msg}", err=True
            )

    except ValueError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        click.echo("\nTo view balances, you need:")
        click.echo("- API_KEY (required)")
        click.echo("- PRIVATE_KEY (required)")
    except Exception as e:
        click.echo(f"❌ Error getting balances: {e}", err=True)
        click.echo("\nNote: Balance retrieval requires valid credentials.")
        click.echo("Check your API_KEY and PRIVATE_KEY.")
