
// Confirm before deleting a video
document.addEventListener("DOMContentLoaded", function () {

    const deleteForms = document.querySelectorAll(".actions form");

    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {

            const confirmDelete = confirm(
                "Are you sure you want to delete this video?"
            );

            if (!confirmDelete) {
                event.preventDefault();
            }

        });
    });

    // Display selected video filename
    const videoInput = document.querySelector('input[name="video"]');

    if (videoInput) {
        videoInput.addEventListener("change", function () {
            if (this.files.length > 0) {
                console.log("Selected video: " + this.files[0].name);
            }
        });
    }

});
