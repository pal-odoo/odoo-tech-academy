from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Offer related to a property"

    price = fields.Float()
    status = fields.Selection([("accepted", "Accepted"), ("refused", "Refused")], copy=False)
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            prop = self.env["estate.property"].browse(vals["property_id"])
            prop.state = "offer_received"
            if not prop.offer_ids:
                continue
            min_price = min(prop.offer_ids.mapped("price"))
            if vals["price"] <= min_price:
                raise UserError(_("The price of the offer must be higher than %s", min_price))
        return super().create(vals_list)
