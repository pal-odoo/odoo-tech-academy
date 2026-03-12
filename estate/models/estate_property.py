from odoo import api, fields, models, exceptions
from odoo.tools import float_compare
from datetime import timedelta


class Estate_property(models.Model):
    _name = "estate.property"
    _description = "Model to modelize Real Estate objects"
    _order = "id desc"

    name = fields.Char(string="Name", required=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Datetime(copy=False, default=fields.Date.today() + timedelta(days=90))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Selection(
        string='Orientation',
        selection=[('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')],
        help="Orientation is meant to describe the garden."
    )
    active = fields.Boolean('Active', default=True)
    state = fields.Selection(
        string='Status',
        selection=[('new', 'New'), ('offer_received', 'Offer Received'), ('offer_accepted', 'Offer Accepted'), ('sold', 'Sold'), ('cancelled', 'Cancelled')],
        help="State is meant to describe the evolution.",
        default='new',
        copy=False
    )
    buyer_id = fields.Many2one("res.partner")
    seller_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    property_type_id = fields.Many2one("estate.property.type")
    property_tag_ids = fields.Many2many("estate.property.tags")
    property_offer_ids = fields.One2many("estate.property.offer", "property_id")
    total_area = fields.Float(compute="_compute_area")
    best_offer_price = fields.Float(compute="_compute_best_offer")
    agency_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.user.company_id)

    _check_expected_price_positive = models.Constraint(
        'CHECK(expected_price > 0)',
        'The Property\'s expected price must be positive.',
    )
    _check_selling_price_positive = models.Constraint(
        'CHECK(selling_price >= 0)',
        'The Property\'s selling price must be positive.',
    )

    @api.depends("garden_area", "living_area")
    def _compute_area(self):
        for prop in self:
            prop.total_area = prop.garden_area + prop.living_area

    @api.depends("property_offer_ids.price")
    def _compute_best_offer(self):
        for prop in self:
            if prop.property_offer_ids and prop.state in {'offer_accepted', 'sold'}:
                prop.best_offer_price = max(prop.property_offer_ids.mapped("price"))
            else:
                prop.best_offer_price = 0

    @api.onchange("garden")
    def _onchange_garden(self):
        self.garden_area = 10 if self.garden else 0
        self.garden_orientation = "north" if self.garden else False

    def sell_property(self):
        for prop in self:
            if prop.state == "cancelled":
                raise exceptions.UserError("A Cancelled Property can't be sold")
            prop.state = "sold"
        return True

    def cancel_property(self):
        for prop in self:
            if (prop.state == "sold"):
                raise exceptions.UserError("A Sold Property can't be cancelled")
            prop.state = "cancelled"
        return True

    @api.constrains("expected_price", "selling_price")
    def _onchange_expected_price(self):
        for prop in self:
            if prop.state in {'offer_accepted', 'sold'} \
               and float_compare(prop.expected_price * 90 / 100, prop.selling_price, 2) < 0:
                raise exceptions.ValidationError("The selling price must be equal or higher than 90% of the expected price.")

    def unlink(self):
        for prop in self:
            if prop.state not in {'new', 'cancelled'}:
                raise exceptions.UserError("Only new or cancelled properties can be deleted.")
        return super().unlink()
