"""
Economy commands (browse, buy, sell) for Takomud.
"""

from evennia.commands.command import Command as BaseCommand
from evennia.utils import utils


def _find_merchant(room):
    """Return the first NPC in room with a non-empty db.shop, or None."""
    for obj in room.contents:
        if utils.inherits_from(obj, "typeclasses.npcs.NPC"):
            shop = obj.db.shop
            if shop:
                return obj
    return None


def _entry_proto_key(entry):
    """Return the prototype_key string from a shop entry (str or dict)."""
    if isinstance(entry, dict):
        return entry.get("prototype_key", "")
    return entry


def _entry_price(entry, spawned_item):
    """Return the price for a shop entry, falling back to item.db.value."""
    if isinstance(entry, dict) and "price" in entry:
        return entry["price"]
    return spawned_item.db.value or 0


class CmdBrowse(BaseCommand):
    """
    Browse the wares of a merchant in the room.

    Usage:
      browse
      shop
      wares
    """

    key = "browse"
    aliases = ["shop", "wares"]
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        from evennia.prototypes import spawner

        merchant = _find_merchant(self.caller.location)
        if not merchant:
            self.caller.msg("There is nothing for sale here.")
            return

        shop = merchant.db.shop
        lines = [f"\n|w--- {merchant.key}'s Wares ---|n"]

        stock = merchant.db.shop_stock or {}
        spawned = []
        try:
            for entry in shop:
                proto_key = _entry_proto_key(entry)
                if not proto_key:
                    continue
                qty = stock.get(proto_key, -1)  # -1 = unlimited
                if qty == 0:
                    continue  # out of stock
                try:
                    items = spawner.spawn(proto_key)
                    item = items[0] if items else None
                except Exception:
                    item = None

                if item:
                    price = _entry_price(entry, item)
                    qty_str = f" ({qty} left)" if qty > 0 else ""
                    lines.append(f"  {item.key:<30} — {price} gold{qty_str}")
                    spawned.append(item)
                else:
                    name = proto_key.replace("_", " ").title()
                    price = entry.get("price", "?") if isinstance(entry, dict) else "?"
                    lines.append(f"  {name:<30} — {price} gold")
        finally:
            for item in spawned:
                item.delete()

        if len(lines) == 1:
            self.caller.msg("There is nothing for sale here.")
            return

        self.caller.msg("\n".join(lines))


class CmdBuy(BaseCommand):
    """
    Buy an item from a merchant in the room.

    Usage:
      buy <item name>
    """

    key = "buy"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        from evennia.prototypes import spawner

        if not self.args:
            self.caller.msg("Buy what?")
            return

        want = self.args.strip().lower()

        merchant = _find_merchant(self.caller.location)
        if not merchant:
            self.caller.msg("There is nothing for sale here.")
            return

        shop = merchant.db.shop

        # Search for matching item by spawning each and checking name
        for entry in shop:
            proto_key = _entry_proto_key(entry)
            if not proto_key:
                continue

            try:
                items = spawner.spawn(proto_key)
                item = items[0] if items else None
            except Exception:
                item = None

            if not item:
                continue

            if want in item.key.lower():
                # Check finite stock
                stock = dict(merchant.db.shop_stock or {})
                qty = stock.get(proto_key, -1)
                if qty == 0:
                    item.delete()
                    self.caller.msg(f"|rOut of stock.|n")
                    return
                price = _entry_price(entry, item)
                gold = self.caller.db.gold or 0
                if gold < price:
                    item.delete()
                    self.caller.msg("You cannot afford that.")
                    return
                # Complete the purchase
                self.caller.db.gold = gold - price
                if qty > 0:
                    stock[proto_key] = qty - 1
                    merchant.db.shop_stock = stock
                item.location = self.caller
                self.caller.msg(
                    f"|gYou pay {price} gold and receive {item.key}.|n"
                )
                return
            else:
                item.delete()

        self.caller.msg(f"The merchant doesn't carry anything called '{self.args.strip()}'.")


class CmdSell(BaseCommand):
    """
    Sell an item from your inventory to a merchant in the room.

    Usage:
      sell <item>
    """

    key = "sell"
    locks = "cmd:all()"
    help_category = "General"

    def func(self):
        if not self.args:
            self.caller.msg("Sell what?")
            return

        merchant = _find_merchant(self.caller.location)
        if not merchant:
            self.caller.msg("There is no merchant here to buy your goods.")
            return

        obj = self.caller.search(self.args.strip(), location=self.caller)
        if not obj:
            return

        if not utils.inherits_from(obj, "typeclasses.items.Item"):
            self.caller.msg("You can't sell that.")
            return

        if not obj.db.droppable:
            self.caller.msg(f"|rYou cannot part with {obj.key}.|n")
            return

        value = obj.db.value or 0
        payout = max(value // 2, 1) if value > 0 else 0

        obj.delete()
        self.caller.db.gold = (self.caller.db.gold or 0) + payout
        self.caller.msg(
            f"|gYou sell {obj.key} for {payout} gold.|n"
        )
