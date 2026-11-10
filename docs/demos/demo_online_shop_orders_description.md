This synthetic event log describes how a fictional online shop handles customer orders, from the moment an order arrives until it is closed. All names, people and values are invented.

#### Statistics
- **Domain**: E-commerce: Order-to-delivery process
- **Cases**: 400 orders (`case_id`, e.g. `ORD-1001`)
- **Events**: 5,911 
- **Activities**: 20 
- **Process variants**: 41 different paths through the process
- **Time span**: March - July 2025 

#### Columns
- **case_id**: Order number; all events of one order belong together
- **activity**: The step that was performed, e.g. *Check Stock*
- **timestamp**: When the step was performed (`YYYY-MM-DD HH:MM:SS`)
- **resource**: Who performed it, e.g. an employee or a courier team
- **department**: Department responsible: Sales, Finance, Warehouse, Procurement, Logistics, Customer Service
- **customer_segment**: Standard, Premium or Business customer
- **order_value_eur**: Order value in euros

#### How the process works
1. **Order Received -> Verify Payment.** Every order starts here.
2. **Check Stock**, then one of two paths:
   - Items are in stock -> **Reserve Items** (about 40% of orders)
   - Items are missing -> **Order from Supplier -> Receive Goods -> Inspect Goods** (about 60%). If a supplier delivery is incomplete, the remaining items are ordered again, so this part can repeat.
3. **Pick Items**
4. **Pack Order** and **Send Invoice** (happen at the same time): the warehouse packs while finance sends the invoice, so either one can come first.
5. **Create Shipping Label**, then **Ship Standard** or **Ship Express**. Premium customers mostly choose Express, Standard customers mostly Standard.
6. **Deliver Package**, then either **Confirm Receipt** or **Request Return -> Issue Refund** (about 36% returns).
7. **Close Order**

**Rare case:** In 4 orders the payment fails and the order ends with **Contact Customer -> Cancel Order**. These steps are hidden by the default filters (see the tips below).

#### What to look for with each algorithm
| Algorithm | What you will see |
|---|---|
| **Heuristic Mining** | A clear flow chart with frequencies. Look at the **supplier loop** (arrow from *Inspect Goods* back to *Order from Supplier*) and the split after *Pick Items*. |
| **Fuzzy Mining** | Arrows in **both directions** between *Send Invoice* and *Pack Order*. This is how parallel steps look when only the order of events is counted. |
| **Inductive Mining** | A structured BPMN model with **gateways**: `X` for a choice, `+` for parallel steps. The supplier re-orders appear as a loop around the small **τ** node, a silent step that only routes the flow back. |
| **Inductive Mining Infrequent** | At the default settings, the same model as Inductive Mining, because the dataset contains no noise. Raise the **Noise Threshold** to 0.4 or higher: the supplier part is then drawn as a simple sequence, with only a small loop back. |
| **Alpha Mining** | A **Petri net**. Places circles with several outgoing arrows show choices; a transition feeding two places at once shows parallel steps. |
| **Genetic Mining** | A Petri net found by an evolutionary search. It takes noticeably longer than the other algorithms. |

In **Heuristic** and **Fuzzy Mining**, the thickness of an arrow shows how often that path is taken: thick arrows are the main flow, thin arrows the less frequent paths. The other algorithms draw all connections with the same width.

#### Tips for exploring
- **Make rare behaviour visible:** set **Node Frequency (absolute)** to 4 or less, or **Node Frequency (normalized)** to 0. *Contact Customer* and *Cancel Order* then appear.
  - In **Heuristic** and **Fuzzy Mining**, also set **Edge Frequency (normalized)** to 0, so their arrows *Verify Payment -> Contact Customer -> Cancel Order* are drawn too.
  - In **Inductive Mining**, also lower the **Traces Threshold** to 0.15 or less.
- **Hide less important paths:** raise **Node Frequency (normalized)** step by step (this works the same for all six algorithms):
  - at 0.35 the returns path *Request Return -> Issue Refund* disappears
  - at 0.40 *Reserve Items* disappears
  - at 0.45 *Ship Express* disappears
- **Inspect the file:** use **Download demo dataset** to see what a valid input file looks like. You can upload your own CSV in the same format.