async function postJson(url) {
    const response = await fetch(url, { method: "POST" });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }
    return data;
}

document.querySelectorAll(".delete-user-btn").forEach((button) => {
    button.addEventListener("click", async () => {
        const username = button.dataset.username;
        const ok = window.confirm(`Delete user "${username}"?`);
        if (!ok) return;

        try {
            await postJson(`/admin/delete-user/${encodeURIComponent(username)}`);
            window.location.reload();
        } catch (error) {
            window.alert(error.message);
        }
    });
});

document.querySelectorAll(".delete-image-btn").forEach((button) => {
    button.addEventListener("click", async () => {
        const folder = button.dataset.folder;
        const filename = button.dataset.filename;
        const ok = window.confirm(`Delete image "${filename}" from ${folder}?`);
        if (!ok) return;

        try {
            const url = `/admin/delete-image/${encodeURIComponent(folder)}/${encodeURIComponent(filename)}`;
            await postJson(url);
            window.location.reload();
        } catch (error) {
            window.alert(error.message);
        }
    });
});
