Product
=======

Fields
######
List of all product fields with a breif explanation on whats it's used
for.

UPC (Universal Product Code)
----------------------------
This is an identifier for a product which is not specific to a
particular supplier. Eg. an ISBN for a book. It must be unique!
You can choose not to use this value and in that case, a products
auto-generated ID (integer) will be used instead.

Name
----
This is a products main title. Value is translatable.

Slug
----
This is a value used in the "url" bar and it's used to identify the
product, therefore it must be unique. Value is translatable.

Active
------
This is a flag that indicates if product is visible on site.
Useful for hiding a product instead of actually deleting the record.

Date added / Last modified
--------------------------
Datetime fields for keeping a track of when a product has been created
and modified.

Parent
------
This is a field used to specify if this product is a variant of
another product. Read about it more in
`How to add a variant of a product?`_ section.

Featured image
--------------
Main image for this product.

Categorization
--------------
Thease are optional fields for categorizing a product. There are
separeted into **Category**, **Brand** and **Manufacturer**.

Unit price
----------
Main price of a product, it can't be empty.

Discount percent
----------------
This is a percent value (0-100) representing this products discount.
It can be empty and in case that this is a variant of a product it will
automatically inherit it's parent discount percent. To avoid that on a
product variant, set it explicitly to 0.

Is discountable?
----------------
This flag indicates if this product can be used in an offer or not
when a offer system is used within a shop. This has nothing to do with
a `Discount percent`_ of a product, but helps to disable a
"discount code" to be used with this product.

Quantity
--------
This value is a number of product units currently available to buy.
It can be left empty in which case, a product will be treated as if it's
always available. If a product is out of stock, set quantity value to 0.

Modifiers
---------
You can select modifers that will affect this product in a checkout
process. Read about it more on `Modifiers`_ section.

Measurements
------------
You can add this fields to define product measurements. When product is
a variant, parents values are inherited but can be overidden. In a case
when variant has defined a measurement for eg. 'width' but it's parent
doesn't have that value set, value will be ignored.

Attributes
----------
This fields should only be used when a product is a variant to specify
which attributes this product has. There shouldn't be more than one
products variant with the same attribute combination. You can read more
on `Attributes`_ section.


How to add a variant of a product?
##################################

What classifies a variant product is that is has a `Parent`_ selected
and at least one of `Attributes`_ choosen.

To add a new variant of a product, you need to create a new product
end select a base product as it's parent, then add an attribute to it
eg. ``color: Blue``.

To add a variant more easily when looking at a product or a variant of a
product you wish to add a new variant, simply click on
**"Add a variant"** button in the top right corner of the screen.
This will prepopulate the `Parent`_ field aswell as start you of with a
unique `Name`_ and `Slug`_ values you can change. All thats left to do
then is add `Attributes`_ and save the product.
