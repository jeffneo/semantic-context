// Database: memory (what Virtual Graph reads fetched)
// Is this customer remembered? 0 until a recall fetches them. ($customer is the one chosen for you: a customer with calls and card activity, not yet remembered.)
MATCH (c:Customer {cif_number: $customer})
RETURN count(c) AS remembered
