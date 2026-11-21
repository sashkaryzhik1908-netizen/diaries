// Данные ранее отправленной формы
const savedFormData = window.savedFormData;

// ==========================================
// MULTISELECT
// ==========================================
function addOption(variableName) {
    const select = document.getElementById("select_" + variableName);
    const list = document.getElementById("selected_" + variableName);
    const result = document.getElementById("result_" + variableName);
    const optionId = select.value;

    if (!optionId) return;

    const exists = Array.from(list.children).some(
        item => item.dataset.id === optionId
    );

    if (exists) return;

    const optionText = select.options[select.selectedIndex].text;
    const item = document.createElement("div");
    item.className = "list-group-item";
    item.dataset.id = optionId;

    const row = document.createElement("div");
    row.className = "d-flex justify-content-between align-items-center";

    const text = document.createElement("span");
    text.textContent = optionText;

    const buttons = document.createElement("div");

    const upButton = document.createElement("button");
    upButton.type = "button";
    upButton.className = "btn btn-sm btn-outline-secondary me-1";
    upButton.textContent = "↑";
    upButton.onclick = () => moveUp(item);

    const downButton = document.createElement("button");
    downButton.type = "button";
    downButton.className = "btn btn-sm btn-outline-secondary me-1";
    downButton.textContent = "↓";
    downButton.onclick = () => moveDown(item);

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "btn btn-sm btn-outline-danger";
    removeButton.textContent = "Удалить";
    removeButton.onclick = () => {
        item.remove();
        updateResult(list, result);
    };

    buttons.append(upButton, downButton, removeButton);
    row.append(text, buttons);
    item.appendChild(row);

    if (variableName === "drug") {
        const doseInput = document.createElement("input");
        doseInput.type = "text";
        doseInput.className = "form-control mt-2";
        doseInput.placeholder = "Введите дозировку";
        doseInput.name = `dose_${optionId}`;
        doseInput.value = getSavedDose(optionId);
        item.appendChild(doseInput);
    }

    list.appendChild(item);
    updateResult(list, result);
}

function getSavedDose(optionId) {
    const saved = savedFormData[`dose_${optionId}`];
    return Array.isArray(saved) ? saved[0] || "" : saved || "";
}

function moveUp(item) {
    const previous = item.previousElementSibling;

    if (previous) {
        item.parentNode.insertBefore(item, previous);
    }

    const list = item.parentNode;
    const variableName = list.id.replace("selected_", "");
    const result = document.getElementById("result_" + variableName);

    updateResult(list, result);
}

function moveDown(item) {
    const next = item.nextElementSibling;

    if (next) {
        item.parentNode.insertBefore(next, item);
    }

    const list = item.parentNode;
    const variableName = list.id.replace("selected_", "");
    const result = document.getElementById("result_" + variableName);

    updateResult(list, result);
}

function updateResult(list, result) {
    const selectedIds = Array.from(list.children).map(
        item => item.dataset.id
    );

    result.value = selectedIds.join(",");
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('[id^="result_"]').forEach(result => {
        const variableName = result.id.replace("result_", "");
        const select = document.getElementById("select_" + variableName);
        const list = document.getElementById("selected_" + variableName);

        if (!select || !list || !result.value) return;

        const selectedIds = result.value.split(",");

        selectedIds.forEach(optionId => {
            const option = Array.from(select.options).find(
                item => item.value === optionId
            );

            if (option) {
                select.value = optionId;
                addOption(variableName);
            }
        });
    });
});

// ==========================================
// НАЗНАЧЕНИЯ
// ==========================================
document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("prescription-rows");
    const addButton = document.getElementById("add-prescription");

    if (!container || !addButton) return;

    function getSavedValue(name) {
        return savedFormData[name]?.[0] || "";
    }

    function getSavedList(name) {
        return savedFormData[name] || [];
    }

    function updateGroupNames(row, index) {
        row.dataset.groupIndex = index;

        row.querySelector('[name^="purpose_id"]').name =
            `purpose_id[${index}]`;

        row.querySelector('[name^="administration_method"]').name =
            `administration_method[${index}]`;

        row.querySelector('[name^="frequency"]').name =
            `frequency[${index}]`;

        row.querySelector('[name^="start_date"]').name =
            `start_date[${index}]`;

        row.querySelectorAll(".medication-row").forEach(medicationRow => {
            const selects = medicationRow.querySelectorAll("select");

            selects[0].name = `medication_id[${index}][]`;
            selects[1].name = `unit[${index}][]`;

            medicationRow.querySelector("input").name =
                `dose[${index}][]`;
        });
    }

    function reindexGroups() {
        container.querySelectorAll(".prescription-row").forEach(
            (row, index) => updateGroupNames(row, index)
        );
    }

    function restoreGroups() {
        const purposeKeys = Object.keys(savedFormData)
            .filter(key => /^purpose_id\[\d+\]$/.test(key))
            .sort((a, b) => Number(a.match(/\d+/)[0]) -
                Number(b.match(/\d+/)[0]));

        if (!purposeKeys.length) return;

        const templateRow = container
            .querySelector(".prescription-row")
            .cloneNode(true);

        container.innerHTML = "";

        purposeKeys.forEach((key, groupPosition) => {
            const oldIndex = key.match(/\d+/)[0];
            const row = templateRow.cloneNode(true);

            row.querySelector('[name^="purpose_id"]').value =
                getSavedValue(`purpose_id[${oldIndex}]`);

            row.querySelector('[name^="administration_method"]').value =
                getSavedValue(`administration_method[${oldIndex}]`);

            row.querySelector('[name^="frequency"]').value =
                getSavedValue(`frequency[${oldIndex}]`);

            row.querySelector('[name^="start_date"]').value =
                getSavedValue(`start_date[${oldIndex}]`);

            const medicationIds = getSavedList(
                `medication_id[${oldIndex}][]`
            );

            const doses = getSavedList(`dose[${oldIndex}][]`);
            const units = getSavedList(`unit[${oldIndex}][]`);

            const medicationsContainer = row.querySelector(
                ".medications-container"
            );

            const medicationTemplate = medicationsContainer
                .querySelector(".medication-row")
                .cloneNode(true);

            medicationsContainer.innerHTML = "";

            medicationIds.forEach((medicationId, medicationIndex) => {
                const medicationRow = medicationTemplate.cloneNode(true);
                const selects = medicationRow.querySelectorAll("select");

                selects[0].value = medicationId;
                selects[1].value = units[medicationIndex] || "";

                medicationRow.querySelector("input").value =
                    doses[medicationIndex] || "";

                medicationsContainer.appendChild(medicationRow);
            });

            if (!medicationIds.length) {
                medicationsContainer.appendChild(
                    medicationTemplate.cloneNode(true)
                );
            }

            container.appendChild(row);
            updateGroupNames(row, groupPosition);
        });
    }

    container.addEventListener("click", function (event) {
        const target = event.target;

        const addMedicationButton = target.closest(".add-medication");

        if (addMedicationButton) {
            const group = addMedicationButton.closest(".prescription-row");

            const medicationsContainer = group.querySelector(
                ".medications-container"
            );

            const firstMedication = medicationsContainer.querySelector(
                ".medication-row"
            );

            if (!firstMedication) return;

            const newMedication = firstMedication.cloneNode(true);

            newMedication.querySelectorAll("select").forEach(select => {
                select.selectedIndex = 0;
            });

            newMedication.querySelector("input").value = "";

            medicationsContainer.appendChild(newMedication);
            reindexGroups();

            return;
        }

        const removeMedicationButton = target.closest(".remove-medication");

        if (removeMedicationButton) {
            const group = removeMedicationButton.closest(".prescription-row");
            const rows = group.querySelectorAll(".medication-row");

            if (rows.length > 1) {
                removeMedicationButton.closest(".medication-row").remove();
                reindexGroups();
            }

            return;
        }

        const removePrescriptionButton = target.closest(".remove-prescription");

        if (removePrescriptionButton) {
            const rows = container.querySelectorAll(".prescription-row");

            if (rows.length > 1) {
                removePrescriptionButton.closest(".prescription-row").remove();
                reindexGroups();
            }
        }
    });

    addButton.addEventListener("click", function () {
        const firstRow = container.querySelector(".prescription-row");

        if (!firstRow) return;

        const newRow = firstRow.cloneNode(true);

        newRow.querySelectorAll(".medication-row").forEach((row, index) => {
            if (index > 0) row.remove();
        });

        newRow.querySelectorAll("input").forEach(input => {
            input.value = "";
        });

        newRow.querySelectorAll("select").forEach(select => {
            select.selectedIndex = 0;
        });

        container.appendChild(newRow);
        reindexGroups();
    });

    restoreGroups();
    reindexGroups();
});