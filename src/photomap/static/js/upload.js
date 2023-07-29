let fileCount, currentSize, totalSize, failed, imported, duplicates;

function updateBar() {
    let bar = document.getElementById("progress");
    let current = Math.round((imported + failed + duplicates) / fileCount * 100);
    bar.style.width = current + "%";
    bar.innerText = "Processed " + current + "%";
}

function updateProgress() {
    updateBar();
    document.getElementById("imported").innerHTML = "Imported <strong>" + imported + "</strong>";
    document.getElementById("duplicates").innerHTML = "Duplicates <strong>" + duplicates + "</strong>";
    document.getElementById("failed").innerHTML = "Failed <strong>" + failed + "</strong>";
}

function sendFile(file, secret) {
    const xhr = new XMLHttpRequest();
    const fd = new FormData();
    xhr.open("POST", "/upload", true);
    xhr.setRequestHeader("Authentication", secret);
    xhr.onreadystatechange = () => {
        if (xhr.readyState === 4) {
            if (xhr.status === 200)
                imported += 1;
            else if (xhr.status === 409)
                duplicates += 1;
            else {
                failed += 1;
                document.getElementById("errorContent").innerHTML += file.name + " -> " +  xhr.responseText + "<br>";
            }
            currentSize += file.size;
            updateProgress();
        }
    };
    fd.append("filename", file.name);
    fd.append("photo", file);
    // Initiate a multipart/form-data upload
    xhr.send(fd);
}

function initUpload() {
    const uploadInput = document.getElementById("uploadInput");
    uploadInput.addEventListener("change", function () {
        fileCount = 0;
        currentSize = 0;
        totalSize = 0;
        failed = 0;
        imported = 0;
        duplicates = 0;
        let bar = document.getElementById("progress");
        bar.style.width = "0%";
        bar.innerText = "0%";
        for (const file of uploadInput.files) {
            if (!file.type.startsWith("image"))
                continue
            fileCount += 1;
            totalSize += file.size;
        }
        let secret = document.getElementById("secret").value;
        // document.getElementById("totals").innerHTML = `Uploading ${fileCount} files of ${totalSize} bytes`;
        for (const file of uploadInput.files) {
            if (!file.type.startsWith("image"))
                continue
            sendFile(file, secret);
        }

    }
    );
}

window.addEventListener("load", (event) => {
	initUpload();
});
