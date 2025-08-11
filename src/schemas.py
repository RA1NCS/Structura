from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class SubItem(BaseModel):
    nm: str = Field(
        description="Add-on or modifier text (e.g. '+Hot', 'No Ice'). "
        "Output once per modifier listed under a parent menu item; "
        "always present when a modifier line exists."
    )
    unitprice: Optional[str] = Field(
        description="Unit price of the modifier.  Output only if a per-unit "
        "price is printed for the modifier row, as in some café "
        "receipts."
    )
    cnt: Optional[str] = Field(
        description="Quantity of the modifier when it appears (rare in CORD). "
        "Emit only if the receipt shows a numeric or 'x'-style count "
        "next to the modifier."
    )
    price: Optional[str] = Field(
        description="Total price for the modifier (unitprice × cnt) when the "
        "modifier is billed separately.  Emit only if printed."
    )
    etc: Optional[str] = Field(
        description="Any extra notes that the receipt prints on the modifier "
        "line (e.g. 'free' or flavour codes).  Skip if absent."
    )


class MenuItem(BaseModel):
    nm: str = Field(
        description="Main name of the menu line (e.g. 'CAPPUCCINO'). "
        "Always output for every menu entry—this is CORD's "
        "mandatory 'menu.nm'."
    )
    cnt: Optional[str] = Field(
        description="Quantity string (e.g. '2', '2X').  Emit only if the "
        "receipt prints an explicit count.  Omit when the quantity "
        "is implicitly '1' and not written."
    )
    unitprice: Optional[str] = Field(
        description="Per-unit price of the item when printed separately from "
        "the total line price.  Common in restaurant bills; omit "
        "if only the total line price appears."
    )
    price: str = Field(
        description="Total price for this item line.  Always output—this is "
        "CORD's required 'menu.price'."
    )
    num: Optional[str] = Field(
        description="Internal item code or PLU (e.g. '102').  Output when a "
        "numeric/alpha code is shown adjacent to the name.  Skip "
        "for receipts that show no item codes."
    )
    discountprice: Optional[str] = Field(
        description="Absolute discount applied to this item (negative or "
        "parenthesised number).  Emit only when a per-item discount "
        "row exists."
    )
    itemsubtotal: Optional[str] = Field(
        description="Net price after discount for this item (*very* rare in "
        "CORD—present in <1 % of items).  Output only if printed."
    )
    vatyn: Optional[str] = Field(
        description="'Y' or 'N' flag indicating VAT inclusion at line level. "
        "Present in a handful of tax-detailed receipts—omit unless "
        "the receipt shows this flag next to the item."
    )
    etc: Optional[str] = Field(
        description="Miscellaneous notes at the item level (size, prep notes) "
        "when they are printed on the same line as the item; omit "
        "otherwise."
    )
    sub: Optional[List[SubItem]] = Field(
        description="List of modifier objects attached to this item. "
        "Create this list only when at least one modifier line "
        "('menu.sub_*') is detected directly under the item."
    )


class SubTotal(BaseModel):
    subtotal_price: Optional[str] = Field(
        description="Interim total before tax/service.  Output when the "
        "receipt shows a line such as 'SUB-TOTAL 25 000'."
    )
    discount_price: Optional[str] = Field(
        description="Overall discount (e.g. '-10 %' or currency amount) "
        "applied at the bill level.  Emit only if printed."
    )
    service_price: Optional[str] = Field(
        description="Service charge line (e.g. 10 % service).  Output when "
        "present; otherwise omit."
    )
    othersvc_price: Optional[str] = Field(
        description="Any additional service-type surcharge not covered by "
        "standard service charge—rare; output only when shown."
    )
    tax_price: Optional[List[str]] = Field(
        description="Printed tax amount (e.g. VAT/GST).  Emit when a specific "
        "tax line appears in the sub-total block."
    )
    etc: Optional[List[str]] = Field(
        description="Other notes or misc amounts printed in the sub-total "
        "section; omit if not present."
    )


class Total(BaseModel):
    total_price: str = Field(
        description="Final amount due after all adjustments.  Always output—"
        "core 'total.total_price' field."
    )
    cashprice: Optional[str] = Field(
        description="Cash tendered amount, if the receipt shows a CASH line."
    )
    changeprice: Optional[str] = Field(
        description="Change returned to the customer.  Emit when a CHANGE/"
        "CHANGED/KEMBALIAN line is printed."
    )
    creditcardprice: Optional[str] = Field(
        description="Amount paid by credit/debit card (appears on multi-tender "
        "receipts).  Output only when present."
    )
    emoneyprice: Optional[str] = Field(
        description="Amount paid with e-money, points or QR wallets.  Emit "
        "when the receipt prints such a line."
    )
    menutype_cnt: Optional[int] = Field(
        description="Count of distinct menu lines.  CORD annotates this only "
        "when the receipt explicitly states it (e.g. 'ITEM TYPE: 3'). "
        "Skip otherwise—do **not** compute it yourself."
    )
    menuqty_cnt: Optional[int] = Field(
        description="Sum of quantities across items, printed on some POS "
        "receipts (e.g. 'TOTAL QTY 5').  Output only if printed."
    )
    total_etc: Optional[str] = Field(
        description="Any free-text note in the total block (e.g. coupon info). "
        "Emit when present; otherwise omit."
    )


class CORDSchema(BaseModel):
    menu: Union[List[MenuItem], MenuItem] = Field(
        description="Ordered list of all primary menu items.  Always include "
        "at least one element."
    )
    sub_total: Optional[SubTotal] = Field(
        description="Sub-total section.  If the receipt has no sub-total, "
        "return an empty object ({})."
    )
    total: Total = Field(
        description="Grand-total/payment section.  Always include—must contain "
        "'total_price'."
    )

    @field_validator("menu", mode="before")
    def _flatten_single_menu(cls, v):
        if isinstance(v, list) and len(v) == 1:
            return v[0]
        return v

    model_config = dict(populate_by_name=True)


class EmptyJSON(BaseModel):
    RootModel: Any
