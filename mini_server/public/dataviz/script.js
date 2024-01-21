const usedAxes = { x: "", y: "" };

const fileList = document.getElementById("file-list");

async function getFileNames() {
    const data = await fetch("/log_names").then((r) => r.json());
    fileList.innerHTML = "";
    for (const file of data) {
        fileList.innerHTML += `<li class="file-name" id="${file}" onclick="plotData(this)">${file}</li>`;
    }
}

function handleAxis(checkbox, axis) {
    usedAxes[axis] = checkbox.id;
}

async function getDataFromFile(file) {
    const params = new URLSearchParams({ file: file.id }).toString();
    const data = await fetch("/get_log?" + params).then((r) => r.json());
    return data;
}

async function plotData(file) {
    const data = await getDataFromFile(file);
    const columns = Object.keys(data[0]);
    usedAxes.x = columns[0];
    usedAxes.y = columns[1];

    Swal.fire({
        title: "Escolha o eixo X do gráfico",
        html: `<div class="popup-container">${columns.reduce((acc, curr) => {
            return (
                acc +
                `<div class="radio-container"><label for="${curr}">${curr}</label><input type="radio" name="column-radio" id="${curr}" onchange="handleAxis(this, 'x')"></div>`
            );
        }, "")}</div>`,
        confirmButtonText: "Confirmar",
        didClose: () =>
            Swal.fire({
                title: "Escolha o eixo y do gráfico",
                html: `<div class="popup-container">${columns.reduce((acc, curr) => {
                    return (
                        acc +
                        `<div class="radio-container"><label for="${curr}">${curr}</label><input type="radio" name="column-radio" id="${curr}" onchange="handleAxis(this, 'y')"></div>`
                    );
                }, "")}</div>`,
                confirmButtonText: "Confirmar",
            }),
    });
}

getFileNames();
