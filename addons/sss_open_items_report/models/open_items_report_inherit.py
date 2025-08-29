import operator
from datetime import date, datetime
from odoo import api, models
from odoo.tools import float_is_zero


class OpenItemsReport(models.AbstractModel):
    _inherit = "report.account_financial_report.open_items"

    def _get_move_lines_domain_not_reconciled(
            self, company_id, account_ids, partner_ids, only_posted_moves, date_from
    ):
        # Call the parent method to get the base domain
        domain = super()._get_move_lines_domain_not_reconciled(
            company_id, account_ids, partner_ids, only_posted_moves, date_from
        )
        return domain

    def _get_move_lines_domain_with_operating_unit(
            self, company_id, account_ids, partner_ids, only_posted_moves, date_from, operating_unit_id=False
    ):
        # Get base domain
        domain = self._get_move_lines_domain_not_reconciled(
            company_id, account_ids, partner_ids, only_posted_moves, date_from
        )

        # Add operating unit filter via partner if specified
        if operating_unit_id:
            # Instead of filtering move lines directly, we filter by partners that have this operating unit
            partners_with_ou = self.env["res.partner"].search([
                ("operating_unit_id", "=", operating_unit_id)
            ]).ids

            if partners_with_ou:
                # If we already have partner filter, intersect with OU partners
                if partner_ids:
                    # Only keep partners that are both in the original filter AND have the selected OU
                    filtered_partner_ids = list(set(partner_ids) & set(partners_with_ou))
                else:
                    # Use all partners with the selected OU
                    filtered_partner_ids = partners_with_ou

                if filtered_partner_ids:
                    # Update the domain to include only these partners
                    # First, remove any existing partner_id domain
                    domain = [d for d in domain if not (isinstance(d, tuple) and d[0] == 'partner_id')]
                    # Add the new partner filter
                    domain.append(("partner_id", "in", filtered_partner_ids))
                else:
                    # No partners match the criteria, return empty result
                    domain.append(("id", "=", -1))  # This will return no records
            else:
                # No partners have this operating unit, return empty result
                domain.append(("id", "=", -1))

        return domain

    def _get_actual_partner_for_display(self, move_line, child_partners_only=False):
        """
        Get the correct partner to display based on child_partners_only setting.
        If child_partners_only is True, always show the contact (child) instead of parent company.
        """
        if not child_partners_only or not move_line.get("partner_id"):
            return move_line["partner_id"]

        # Get the actual partner record
        partner_id = move_line["partner_id"][0] if isinstance(move_line["partner_id"], tuple) else move_line[
            "partner_id"]
        partner = self.env["res.partner"].browse(partner_id)

        # If this partner has a parent, we might want to find the actual contact used
        if partner.parent_id:
            # This is already a contact, use it
            return (partner.id, partner.name)
        else:
            # This is a parent company, try to find which contact was actually used
            # We can look at the move to see if there's a more specific contact
            move_id = move_line["move_id"][0] if isinstance(move_line["move_id"], tuple) else move_line["move_id"]
            move = self.env["account.move"].browse(move_id)

            # Check if the move has a more specific partner (contact)
            if move.partner_id and move.partner_id.parent_id and move.partner_id.parent_id.id == partner.id:
                # The move actually references a contact of this company
                return (move.partner_id.id, move.partner_id.name)

            # If no specific contact found, check if this company has a default contact
            contacts = self.env["res.partner"].search([("parent_id", "=", partner.id)], limit=1)
            if contacts:
                return (contacts[0].id, contacts[0].name)

            # Fallback to original partner
            return move_line["partner_id"]

    def _get_enhanced_move_data(self, move_lines):
        """
        Get enhanced data (salesperson, operating unit) for all move lines.
        This works regardless of whether recalculation happened.
        """
        enhanced_data = {}

        # Get all unique move IDs
        move_ids = list(set([
            ml["move_id"][0] if isinstance(ml["move_id"], tuple) else ml["move_id"]
            for ml in move_lines if ml.get("move_id")
        ]))

        if not move_ids:
            return enhanced_data

        # Get moves with invoice and sale order relations
        moves_data = self.env["account.move"].browse(move_ids).read([
            "id", "journal_id", "type", "invoice_user_id",
            "invoice_origin", "ref", "partner_id"
        ])
        moves_dict = {move["id"]: move for move in moves_data}

        # Get sale orders if needed
        sale_order_names = []
        for move_data in moves_data:
            if move_data.get("invoice_origin"):
                origins = str(move_data["invoice_origin"]).split(",")
                for origin in origins:
                    origin = origin.strip()
                    if origin and origin.startswith(("SO", "S0")):
                        sale_order_names.append(origin)

        # Fetch sale orders data
        sale_orders_data = {}
        if sale_order_names:
            sale_orders = self.env["sale.order"].search([
                ("name", "in", sale_order_names)
            ]).read(["id", "name", "user_id"])
            sale_orders_data = {so["name"]: so for so in sale_orders}

        # Helper function to get salesperson for a move
        def get_salesperson_for_move(move_data):
            if not move_data:
                return False, ""

            journal = self.env["account.journal"].browse(move_data["journal_id"][0])
            salesperson_id = False
            salesperson_name = ""

            if journal.type in ['sale', 'general']:
                # Method 1: Direct invoice salesperson
                if move_data.get("invoice_user_id"):
                    user = self.env["res.users"].browse(move_data["invoice_user_id"][0])
                    if user.exists():
                        salesperson_id = user.id
                        salesperson_name = user.name

                # Method 2: Sale order salesperson
                elif move_data.get("invoice_origin"):
                    origins = str(move_data["invoice_origin"]).split(",")
                    for origin in origins:
                        origin = origin.strip()
                        if origin in sale_orders_data:
                            so_data = sale_orders_data[origin]
                            if so_data.get("user_id"):
                                user = self.env["res.users"].browse(so_data["user_id"][0])
                                if user.exists():
                                    salesperson_id = user.id
                                    salesperson_name = user.name
                                    break

                # Method 3: Direct SO reference
                elif move_data.get("ref"):
                    ref = str(move_data["ref"]).strip()
                    if ref in sale_orders_data:
                        so_data = sale_orders_data[ref]
                        if so_data.get("user_id"):
                            user = self.env["res.users"].browse(so_data["user_id"][0])
                            if user.exists():
                                salesperson_id = user.id
                                salesperson_name = user.name

            return salesperson_id, salesperson_name

        # Build enhanced data for each move line
        for move_line in move_lines:
            ml_id = move_line["id"]
            move_id = move_line["move_id"][0] if isinstance(move_line["move_id"], tuple) else move_line["move_id"]
            move_data = moves_dict.get(move_id)

            # Get salesperson
            salesperson_id, salesperson_name = get_salesperson_for_move(move_data)

            # Get operating unit (safely)
            operating_unit_id = False
            operating_unit_name = False
            if move_line.get("operating_unit_id"):
                if isinstance(move_line["operating_unit_id"], tuple):
                    operating_unit_id = move_line["operating_unit_id"][0]
                    operating_unit_name = move_line["operating_unit_id"][1]
                else:
                    operating_unit_id = move_line["operating_unit_id"]

            enhanced_data[ml_id] = {
                "salesperson_id": salesperson_id,
                "salesperson_name": salesperson_name,
                "operating_unit_id": operating_unit_id,
                "operating_unit_name": operating_unit_name,
                "move_id": move_id,
            }

        return enhanced_data

    def _filter_by_salesperson(self, move_lines, enhanced_data, salesperson_id):
        """Filter move lines by salesperson using enhanced data"""
        if not salesperson_id:
            return move_lines

        filtered_lines = []
        for move_line in move_lines:
            ml_id = move_line["id"]
            if ml_id in enhanced_data:
                if enhanced_data[ml_id]["salesperson_id"] == salesperson_id:
                    filtered_lines.append(move_line)

        return filtered_lines

    def _filter_by_operating_unit(self, move_lines, operating_unit_id):
        """Filter move lines by operating unit via partner"""
        if not operating_unit_id:
            return move_lines

        # Get partners with this operating unit
        partners_with_ou = self.env["res.partner"].search([
            ("operating_unit_id", "=", operating_unit_id)
        ]).ids

        if not partners_with_ou:
            return []

        filtered_lines = []
        for move_line in move_lines:
            partner_id = move_line["partner_id"][0] if isinstance(move_line["partner_id"], tuple) else move_line[
                "partner_id"]
            if partner_id in partners_with_ou:
                filtered_lines.append(move_line)

        return filtered_lines

    def _get_partner_sort_key(self, partner_name):
        """
        Get sorting key for partner name, ignoring CV. and PT. prefixes
        """
        if not partner_name:
            return ""

        # Convert to uppercase for case-insensitive sorting
        name = partner_name.upper().strip()

        # Remove CV. and PT. prefixes for sorting
        if name.startswith("CV."):
            name = name[3:].strip()
        elif name.startswith("PT."):
            name = name[3:].strip()

        return name

    def _format_partner_name_with_ref(self, partner_id, partner_name):
        """
        Format partner name with ref code like [CU123A] Partner Name
        """
        if not partner_id or partner_id == 0:
            return partner_name

        partner_record = self.env["res.partner"].browse(partner_id)
        if not partner_record.exists():
            return partner_name

        # Get the ref field from partner
        partner_ref = partner_record.ref
        if partner_ref:
            return f"[{partner_ref}] {partner_name}"
        else:
            return partner_name

    def _get_data(
            self,
            account_ids,
            partner_ids,
            date_at_object,
            only_posted_moves,
            company_id,
            date_from,
            operating_unit_id=False,
            salesperson_id=False,
            child_partners_only=False,
            date_to=False,
    ):
        # Get base domain WITHOUT operating unit/salesperson filtering initially
        domain = self._get_move_lines_domain_not_reconciled(
            company_id, account_ids, partner_ids, only_posted_moves, date_from
        )

        ml_fields = [
            "id",
            "name",
            "date",
            "move_id",
            "journal_id",
            "account_id",
            "partner_id",
            "amount_residual",
            "date_maturity",
            "ref",
            "debit",
            "credit",
            "reconciled",
            "currency_id",
            "amount_currency",
            "amount_residual_currency",
            "operating_unit_id",
        ]

        move_lines = self.env["account.move.line"].search_read(
            domain=domain, fields=ml_fields
        )

        # Handle recalculation for past dates
        if date_at_object < date.today():
            (
                acc_partial_rec,
                debit_amount,
                credit_amount,
            ) = self._get_account_partial_reconciled(company_id, date_at_object)
            if acc_partial_rec:
                ml_ids = list(map(operator.itemgetter("id"), move_lines))
                debit_ids = list(
                    map(operator.itemgetter("debit_move_id"), acc_partial_rec)
                )
                credit_ids = list(
                    map(operator.itemgetter("credit_move_id"), acc_partial_rec)
                )
                move_lines = self._recalculate_move_lines(
                    move_lines,
                    debit_ids,
                    credit_ids,
                    debit_amount,
                    credit_amount,
                    ml_ids,
                    account_ids,
                    company_id,
                    partner_ids,
                    only_posted_moves,
                )

        # Filter by date and non-zero amounts
        move_lines = [
            move_line
            for move_line in move_lines
            if move_line["date"] <= date_at_object
               and not float_is_zero(move_line["amount_residual"], precision_digits=2)
        ]

        # Apply simple date_to filter if specified (no recalculation, just date filtering)
        if date_to:
            # Convert string date to date object if needed
            if isinstance(date_to, str):
                date_to_object = datetime.strptime(date_to, "%Y-%m-%d").date()
            else:
                date_to_object = date_to

            move_lines = [
                move_line
                for move_line in move_lines
                if move_line["date"] <= date_to_object
            ]

        # Get enhanced data for all move lines
        enhanced_data = self._get_enhanced_move_data(move_lines)

        # Apply filters AFTER recalculation
        if salesperson_id:
            move_lines = self._filter_by_salesperson(move_lines, enhanced_data, salesperson_id)

        if operating_unit_id:
            move_lines = self._filter_by_operating_unit(move_lines, operating_unit_id)

        # Process move lines for display
        journals_ids = set()
        partners_ids = set()
        partners_data = {}
        open_items_move_lines_data = {}

        for move_line in move_lines:
            journals_ids.add(move_line["journal_id"][0])
            acc_id = move_line["account_id"][0]
            ml_id = move_line["id"]

            # Partners data - use actual partner for display if child_partners_only is enabled
            if move_line["partner_id"]:
                if child_partners_only:
                    partner_display = self._get_actual_partner_for_display(move_line, child_partners_only)
                    prt_id = partner_display[0] if isinstance(partner_display, tuple) else partner_display
                    prt_name = partner_display[1] if isinstance(partner_display, tuple) else move_line["partner_id"][1]
                else:
                    prt_id = move_line["partner_id"][0]
                    prt_name = move_line["partner_id"][1]

                # Format partner name with ref code
                prt_name_with_ref = self._format_partner_name_with_ref(prt_id, prt_name)
            else:
                prt_id = 0
                prt_name = "Missing Partner"
                prt_name_with_ref = "Missing Partner"

            if prt_id not in partners_ids:
                partners_data.update({prt_id: {"id": prt_id, "name": prt_name_with_ref}})
                partners_ids.add(prt_id)

            # Move line calculations
            original = 0
            if not float_is_zero(move_line["credit"], precision_digits=2):
                original = move_line["credit"] * (-1)
            if not float_is_zero(move_line["debit"], precision_digits=2):
                original = move_line["debit"]

            if move_line["ref"] == move_line["name"]:
                if move_line["ref"]:
                    ref_label = move_line["ref"]
                else:
                    ref_label = ""
            elif not move_line["ref"]:
                ref_label = move_line["name"]
            elif not move_line["name"]:
                ref_label = move_line["ref"]
            else:
                ref_label = move_line["ref"] + str(" - ") + move_line["name"]

            # Get enhanced data
            enhanced_info = enhanced_data.get(ml_id, {})
            salesperson_id_val = enhanced_info.get("salesperson_id", False)
            salesperson_name_val = enhanced_info.get("salesperson_name", "")
            operating_unit_id_val = enhanced_info.get("operating_unit_id", False)
            operating_unit_name_val = enhanced_info.get("operating_unit_name", False)

            # Calculate amount paid
            amount_paid = original - move_line["amount_residual"]

            move_line.update(
                {
                    "date": move_line["date"],
                    "date_maturity": move_line["date_maturity"]
                                     and move_line["date_maturity"].strftime("%d/%m/%Y"),
                    "original": original,
                    "amount_paid": amount_paid,
                    "partner_id": prt_id,
                    "partner_name": prt_name_with_ref,  # Use formatted name with ref
                    "ref_label": ref_label,
                    "journal_id": move_line["journal_id"][0],
                    "move_name": move_line["move_id"][1],
                    "entry_id": move_line["move_id"][0],
                    "currency_id": move_line["currency_id"][0]
                    if move_line["currency_id"]
                    else False,
                    "currency_name": move_line["currency_id"][1]
                    if move_line["currency_id"]
                    else False,
                    "operating_unit_id": operating_unit_id_val,
                    "operating_unit_name": operating_unit_name_val,
                    "salesperson_id": salesperson_id_val,
                    "salesperson_name": salesperson_name_val,
                }
            )

            # Open Items Move Lines Data
            if acc_id not in open_items_move_lines_data.keys():
                open_items_move_lines_data[acc_id] = {prt_id: [move_line]}
            else:
                if prt_id not in open_items_move_lines_data[acc_id].keys():
                    open_items_move_lines_data[acc_id][prt_id] = [move_line]
                else:
                    open_items_move_lines_data[acc_id][prt_id].append(move_line)

        journals_data = self._get_journals_data(list(journals_ids))
        accounts_data = self._get_accounts_data(open_items_move_lines_data.keys())

        return (
            move_lines,
            partners_data,
            journals_data,
            accounts_data,
            open_items_move_lines_data,
        )

    @api.model
    def _order_open_items_by_date(
            self, open_items_move_lines_data, show_partner_details
    ):
        new_open_items = {}
        if not show_partner_details:
            for acc_id in open_items_move_lines_data.keys():
                new_open_items[acc_id] = {}
                move_lines = []
                for prt_id in open_items_move_lines_data[acc_id]:
                    for move_line in open_items_move_lines_data[acc_id][prt_id]:
                        move_lines += [move_line]
                move_lines = sorted(move_lines, key=lambda k: (k["date"]))
                new_open_items[acc_id] = move_lines
        else:
            for acc_id in open_items_move_lines_data.keys():
                new_open_items[acc_id] = {}

                # Get partners data for sorting
                partners_with_names = []
                for prt_id in open_items_move_lines_data[acc_id]:
                    # Get partner name from the first move line in this partner group
                    first_move_line = open_items_move_lines_data[acc_id][prt_id][0]
                    partner_name_with_ref = first_move_line.get('partner_name', '')

                    # Extract the actual name for sorting (remove ref code)
                    # If name is like "[CU123A] Bob", extract "Bob"
                    if partner_name_with_ref.startswith('[') and '] ' in partner_name_with_ref:
                        partner_name_for_sort = partner_name_with_ref.split('] ', 1)[1]
                    else:
                        partner_name_for_sort = partner_name_with_ref

                    partners_with_names.append((prt_id, partner_name_with_ref, partner_name_for_sort))

                # Sort partners by name (ignoring CV. and PT. prefixes)
                partners_with_names.sort(key=lambda x: self._get_partner_sort_key(x[2]))

                # Build ordered dictionary based on sorted partners
                for prt_id, partner_name_with_ref, partner_name_for_sort in partners_with_names:
                    new_open_items[acc_id][prt_id] = {}
                    move_lines = []
                    for move_line in open_items_move_lines_data[acc_id][prt_id]:
                        move_lines += [move_line]
                    move_lines = sorted(move_lines, key=lambda k: (k["date"]))
                    new_open_items[acc_id][prt_id] = move_lines
        return new_open_items

    def _get_report_values(self, docids, data):
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        company_id = data["company_id"]
        account_ids = data["account_ids"]
        partner_ids = data["partner_ids"]
        date_at = data["date_at"]
        date_at_object = datetime.strptime(date_at, "%Y-%m-%d").date()
        date_from = data["date_from"]
        only_posted_moves = data["only_posted_moves"]
        show_partner_details = data["show_partner_details"]
        operating_unit_id = data.get("operating_unit_id", False)
        salesperson_id = data.get("salesperson_id", False)
        child_partners_only = data.get("child_partners_only", False)
        date_to = data.get("date_to", False)

        (
            move_lines_data,
            partners_data,
            journals_data,
            accounts_data,
            open_items_move_lines_data,
        ) = self._get_data(
            account_ids,
            partner_ids,
            date_at_object,
            only_posted_moves,
            company_id,
            date_from,
            operating_unit_id,
            salesperson_id,
            child_partners_only,
            date_to,
        )

        total_amount = self._calculate_amounts(open_items_move_lines_data)
        open_items_move_lines_data = self._order_open_items_by_date(
            open_items_move_lines_data, show_partner_details
        )

        # Get operating unit name for display
        operating_unit_name = ""
        if operating_unit_id:
            operating_unit = self.env["operating.unit"].browse(operating_unit_id)
            operating_unit_name = operating_unit.name if operating_unit.exists() else ""

        # Get salesperson name for display
        salesperson_name = ""
        if salesperson_id:
            salesperson = self.env["res.users"].browse(salesperson_id)
            salesperson_name = salesperson.name if salesperson.exists() else ""

        # Get date_to for display
        date_to_display = ""
        if date_to:
            if isinstance(date_to, str):
                date_to_display = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
            else:
                date_to_display = date_to.strftime("%d/%m/%Y")

        # Call parent method and update with our additions
        report_values = super()._get_report_values(docids, data)
        report_values.update({
            "operating_unit_name": operating_unit_name,
            "salesperson_name": salesperson_name,
            "child_partners_only": child_partners_only,
            "date_to": date_to_display,
        })

        # Update the data we processed with operating unit filtering
        report_values.update({
            "journals_data": journals_data,
            "partners_data": partners_data,
            "accounts_data": accounts_data,
            "total_amount": total_amount,
            "Open_Items": open_items_move_lines_data,
        })

        return report_values