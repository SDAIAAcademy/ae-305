"""The text of Wahaj's synthetic maintenance manuals, versions 3 and 4 (used by prepare_data.py).

Every procedure is invented for the course. It is not engineering guidance.
"""

V3 = {
    "MM-01": ("Isolation and earthing before work", [
        ("Scope", "This manual applies to every crew working on Wahaj medium-voltage feeders and ring main units. "
                  "No work starts on a conductor until the isolation is complete and recorded."),
        ("Isolation steps", "1. Obtain the switching programme from the control room. 2. Open the feeder breaker and the "
                            "load-break switch. 3. Lock and tag every isolation point with the crew lock. 4. Prove dead with an "
                            "approved voltage tester, tested before and after use. 5. Apply earths on both sides of the work "
                            "point. 6. Record the permit number with the control room."),
        ("Returning to service", "Remove earths only after every crew member has signed off the permit. The control room "
                                 "closes the breaker; a crew never re-energises a feeder."),
    ]),
    "MM-02": ("Ring main unit switching", [
        ("Before switching", "Check the gas pressure gauge of the ring main unit. A gauge in the red zone means no "
                             "switching: report it to the control room and wait for a specialist."),
        ("Switching sequence", "1. Confirm the switching programme number. 2. Check the gas pressure. 3. Operate the "
                               "load-break switch with the insulated handle. 4. Confirm the indicator shows open. "
                               "5. Report the new state to the control room."),
        ("Faults during switching", "If the switch does not move, stop. Do not force the handle. Report the unit number."),
    ]),
    "MM-03": ("Transformer oil sampling", [
        ("When to sample", "Sample distribution transformers above 500 kVA every twelve months and after any fault trip."),
        ("Sampling steps", "Use a clean glass bottle, flush the valve with one litre, fill to the shoulder, and label the "
                           "bottle with the transformer number and the date."),
        ("Results", "A dielectric strength below 30 kV in the laboratory result means the oil must be treated or replaced."),
    ]),
    "MM-04": ("Cable fault location", [
        ("Method", "Locate cable faults by pre-location with a reflectometer, then pinpoint with an acoustic detector."),
        ("Safety", "A cable under test is treated as live. Discharge it to earth after every test."),
        ("Excavation", "Request utility drawings and mark other services before any excavation."),
    ]),
    "MM-05": ("Overhead line patrol", [
        ("Patrol interval", "Patrol overhead feeders every six months, and within 48 hours after a storm or a sand storm."),
        ("What to record", "Record damaged insulators, leaning poles, broken cross-arms and vegetation inside the clearance."),
        ("Insulators", "Report cracked or flashed insulators with the pole number and a photograph."),
    ]),
    "MM-06": ("Vegetation clearance", [
        ("Clearance distances", "Keep trees at least 3 metres from 13.8 kV conductors and 4 metres from 33 kV conductors."),
        ("Palm trees", "Palm fronds are cut back to 4 metres from any conductor, whatever the voltage."),
        ("Landowners", "Inform the landowner before cutting on private land, through the customer-care team."),
    ]),
    "MM-07": ("Heat stress and work-rest", [
        ("Heat index", "Above a heat index of 46 degrees, outdoor work follows a cycle of 40 minutes of work and 20 of rest."),
        ("Water", "Each crew member drinks at least 250 ml of water every 20 minutes in summer."),
        ("Signs", "Stop work and cool the person at once on confusion, headache or no sweating; call the duty medic."),
    ]),
    "MM-08": ("Arc-flash protective equipment", [
        ("Categories", "Switching inside a ring main unit needs category 2 arc-rated clothing; work on an open "
                       "low-voltage board needs category 4."),
        ("Inspection", "Inspect arc-rated clothing before each shift and withdraw any item with holes or contamination."),
    ]),
    "MM-09": ("Restoration priority", [
        ("Priority order", "Restore in this order: hospitals and dialysis centres, water pumping stations, mosques during "
                           "prayer times declared by the control room, then residential feeders by customer count."),
        ("Life-support customers", "Customers registered for medical equipment are called by customer care within 30 minutes "
                                   "of an outage on their feeder."),
    ]),
    "MM-10": ("Customer data in the field", [
        ("What crews may see", "Crews see the account number and the address of the outage only. Phone numbers stay with "
                               "customer care."),
        ("Recording", "Never write customer names or phone numbers in work notes or chat messages; use the account number."),
    ]),
}

V4_CHANGES = {
    # MM-02 revised: a new ring main unit model needs the earth switch interlock checked
    "MM-02": ("Ring main unit switching", [
        ("Before switching", "Check the gas pressure gauge of the ring main unit. A gauge in the red zone means no "
                             "switching: report it to the control room and wait for a specialist."),
        ("Switching sequence", "1. Confirm the switching programme number. 2. Check the gas pressure. 3. On R-24 units, "
                               "check the earth switch interlock is engaged. 4. Operate the load-break switch with the "
                               "insulated handle. 5. Confirm the indicator shows open. 6. Report the new state to the "
                               "control room."),
        ("Faults during switching", "If the switch does not move, stop. Do not force the handle. Report the unit number."),
    ]),
    # MM-11 new: salt fog on the coast (the drift of the fault-risk model has a physical cause)
    "MM-11": ("Insulator washing in coastal regions", [
        ("When to wash", "In Al-Sahil, wash overhead insulators every three months, and within two weeks after a salt fog "
                         "warning from the control room."),
        ("Washing steps", "Wash live insulators only with the approved demineralised-water rig, from at least 3 metres, "
                          "starting with the lowest insulator."),
    ]),
}


def version(v: int) -> dict:
    docs = dict(V3)
    if v >= 4:
        docs.update(V4_CHANGES)
    return docs


def to_markdown(doc_id: str, title: str, sections: list) -> str:
    out = [f"# {doc_id} · {title}", ""]
    for i, (head, body) in enumerate(sections, 1):
        out += [f"## {i}. {head}", "", body, ""]
    return "\n".join(out)
