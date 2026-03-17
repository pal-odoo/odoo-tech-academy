from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Offer related to a property"

    price = fields.Float()
    status = fields.Selection([("accepted", "Accepted"), ("refused", "Refused")], copy=False)
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)
    validity = fields.Integer("Validity (days)", default=7)
    date_deadline = fields.Date("Deadline", compute="_compute_date_deadline", inverse="_inverse_date_deadline")

    @api.depends("validity", "create_date")
    def _compute_date_deadline(self):
        for offer in self:
            create_date = offer.create_date or fields.Date.today()
            offer.date_deadline = fields.Date.add(create_date, days=offer.validity)

    def _inverse_date_deadline(self):
        for offer in self:
            offer.validity = (offer.date_deadline - fields.Date.to_date(offer.create_date)).days

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

    def action_accept_offer(self):
        self.status = "accepted"
        for offer in self:
            offer.property_id.selling_price = offer.price
            offer.property_id.buyer_id = offer.partner_id

    def action_decline_offer(self):
        self.status = "refused"
