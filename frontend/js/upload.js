let selectedFile = null;

const fileInput = document.getElementById("fileInput");

const chooseBtn = document.getElementById("chooseBtn");

const dropArea = document.getElementById("dropArea");

const uploadBtn = document.getElementById("uploadBtn");


// OPEN FILE PICKER
chooseBtn.addEventListener("click", function () {

    fileInput.click();
});


// FILE SELECTED
fileInput.addEventListener("change", function (e) {

    selectedFile = e.target.files[0];

    console.log("Selected File:", selectedFile);

    if (selectedFile) {

        document.getElementById(
            "selectedFileName"
        ).innerText = selectedFile.name;
    }
});


// DRAG OVER
dropArea.addEventListener("dragover", function (e) {

    e.preventDefault();
});


// DROP FILE
dropArea.addEventListener("drop", function (e) {

    e.preventDefault();

    selectedFile = e.dataTransfer.files[0];

    console.log("Dropped File:", selectedFile);

    if (selectedFile) {

        document.getElementById(
            "selectedFileName"
        ).innerText = selectedFile.name;
    }
});


// UPLOAD FILE
async function uploadFile() {

    if (!selectedFile) {

        alert("Please choose a file first");

        return;
    }

    loader.classList.remove("hidden");

    const formData = new FormData();

    formData.append("file", selectedFile);

    try {

        const response = await fetch(
            "/api/v1/admin/migration/upload",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        loader.classList.add("hidden");

        if (data.error) {

            alert(data.error);

            return;
        }

        // SUCCESS MESSAGE
        alert("File uploaded and cleaned successfully");

        // HIDE BUTTONS AFTER SUCCESS
        chooseBtn.style.display = "none";

        uploadBtn.style.display = "none";

        // UPDATE BOX MESSAGE
        dropArea.innerHTML = `
            <h3>File Uploaded Successfully ✅</h3>
            <p>Cleaned file saved successfully.</p>
        `;

    } catch (error) {

        console.error(error);

        loader.classList.add("hidden");

        alert("Upload failed");
    }
}