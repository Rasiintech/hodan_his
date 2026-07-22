frappe.ui.form.on("IPC Compliance Checklist", {
    onload(frm) {
        const load_rows = (tablefield, rows, key = "question") => {
            if (!frm.doc[tablefield] || frm.doc[tablefield].length === 0) {
                rows.forEach(value => {
                    const row = frm.add_child(tablefield);
                    row[key] = value;
                });
                frm.refresh_field(tablefield);
            }
        };

        load_rows("part_1_hand_hygiene", [
            "Are soap and water available at all hand-washing stations?",
            "Do staff follow the 5 moments of international hand hygiene?",
            "Do staff wash hands before and after patient contacts?",
            "Do the staff use hand sanitizer before and after touching a patient?",
            "Are alcohol-based hand rub dispenser installed at every point of station?",
            "Are the hand sanitizers empty or full?",
            "Are paper towels available for drying hands after washing?"
        ]);

        load_rows("part_2_ppe", [
            "Do staff wear PPE correctly when required?",
            "Do staff wear N95 mask when caring for patients with infectious disease?",
            "Are PPE disposed of properly after use?"
        ]);

        load_rows("part_3_waste_management", [
            "Are waste segregated and placed in its designated color-coded bins?",
            "Are sharps containers available at the patient room?",
            "Are sharps disposed of in safe boxes?",
            "Is the sharps box closed/sealed when it reaches 3/4 full?",
            "Are waste collected and transported safely?"
        ]);

        load_rows("part_4_environmental_cleaning", [
            "Are patient rooms cleaned at least 3-times a day?",
            "Are patient beds and surrounding areas cleaned regularly?",
            "Are toilet seats, lids and sinks cleaned and disinfected every day?",
            "Are the floors, walls, windows and doors clean in all areas of the hospital?",
            "Are the correct concentration of chlorine/bleach (0.1%) used for disinfected?",
            "Are buckets, towels and mops cleaned and dried after each use?",
            "Do the Cleaning staff use PPE at all times?",
            "Are disinfected frequently touched surfaces like door handles?",
            "Are high-touch surfaces cleaning and disinfected such; Monitor buttons, Ventilator Surfaces, Infusion pumps and bed rails?"
        ]);

        load_rows("part_5_patient_care", [
            "Do the nurses staff use aseptic technique when insertion IV cannulas and catheter into patients?",
            "Are sterile gauze and sterile gloves used when changing wound dressings?"
        ]);

        load_rows("part_6_patient_isolation", [
            "Are patient beds at least 1 meter apart to avoid crowding and the spread of infectious diseases?",
            "The patients having contagious diseases are they separated?",
            "The patients having infectious do they have an isolation room separated?",
            "Do staff follow IPC protocol contact, droplet and airborne disease precautions?"
        ]);

        load_rows("part_7_medical_equipment", [
            "Are medical instruments cleaned and disinfected/sterilized?",
            "Are shared medical devices such as BP cuffs, thermometers, stethoscopes, SPO2monitors and suction machine disinfected after each use?"
        ]);

        load_rows("part_8_cssd", [
            "Are instruments pre-cleaned before manual or machine washing?",
            "Are appropriate detergents and disinfectants used for the equipment?",
            "Are instruments properly arranged in trays/packs for sterilization?",
            "Are lumened instruments correctly cleaned and disinfected?",
            "Are appropriate chemical indicators used for the equipment?",
            "Are sterilized packs labeled with date, contents and expiry date?",
            "Are sterilized instruments stored in a clean, dry and dust-free area?",
            "Do staff wear the correct Personal Protective Equipment?"
        ]);

        load_rows("part_9_laundry_cleaning", [
            "Are infected/dirty bed sheets collected and transported separately?",
            "Is there a designated trolley for transporting infectious laundry?",
            "Are the infected bed sheets washing in a separate machine?",
            "Are appropriate disinfectants and detergents used for infectious laundry?",
            "Do staff laundry wear the correct use appropriate-PPE?"
        ]);

        load_rows("part_10_restaurant_cleaning", [
            "Is the kitchen clean?",
            "Do the kitchen staff maintain good personal hygiene?",
            "Do the kitchen staff wash their hands before and after preparing food?",
            "Do staff kitchen wear the correct use appropriate-PPE?",
            "Raw foods separated from cooked/ready-to-eat foods?",
            "Is the waste placed in a designated waste bin with a cover?"
        ]);

        load_rows("part_11_score_supervision", [
            "Hand Hygiene Practice",
            "Personal Protective Equipment-PPE",
            "Waste management",
            "Environmental Clean and disinfect",
            "Patient Care and Aseptic Technique",
            "Patient Isolation and Precautions",
            "Medical equipment disinfection",
            "Central Sterile Services Department",
            "Laundry Cleaning",
            "Restaurant Staff Cleaning"
        ], "area_observed");
    }
});
