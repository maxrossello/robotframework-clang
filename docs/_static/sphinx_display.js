document.addEventListener("DOMContentLoaded", function() {
    // Find all Robot Framework code blocks
    var blocks = document.querySelectorAll('.highlight-robotframework');

    blocks.forEach(function(block) {
        // Create the header element
        var header = document.createElement('div');
        header.className = 'robot-toggle-header';
        
        // Insert header before the code content (the .highlight div)
        var content = block.querySelector('.highlight');
        if (content) {
            block.insertBefore(header, content);

            // Add click event to toggle visibility
            header.addEventListener('click', function() {
                block.classList.toggle('collapsed');
            });
        }
    });
});
