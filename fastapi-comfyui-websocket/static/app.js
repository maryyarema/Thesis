document.getElementById('uploadForm').onsubmit = async (e) => {
    e.preventDefault();
    const person = document.getElementById('person').files[0];
    const cloth = document.getElementById('cloth').files[0];
    if (!person || !cloth) return alert('Оберіть обидва зображення!');
    const formData = new FormData();
    formData.append('person', person);
    formData.append('cloth', cloth);
    const res = await fetch('/tryon', { method: 'POST', body: formData });
    if (res.ok) {
        const blob = await res.blob();
        document.getElementById('result').src = URL.createObjectURL(blob);
    } else {
        alert('Помилка обробки!');
    }
};