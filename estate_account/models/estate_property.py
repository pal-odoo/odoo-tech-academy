from odoo import Command, models


class EstateProperty(models.Model):
    _inherit = "estate.property"

    def action_sell_property(self):
        sale_journal_id = self.env["account.journal"].search([("type", "=", "sale")], limit=1).id
        vals_list = []
        for property in self:
            vals = {
                "partner_id": property.buyer_id.id,
                "move_type": "out_invoice",
                "journal_id": sale_journal_id,
                "invoice_line_ids": [
                    Command.create({
                        "name": property.name,
                        "quantity": 1,
                        "price_unit": 0.06 * property.selling_price,
                    }),
                    Command.create({
                        "name": "Administration Fees",
                        "quantity": 1,
                        "price_unit": 100,
                    }),
                ]
            }
            vals_list.append(vals)
        self.env["account.move"].create(vals_list)
        return super().action_sell_property()
