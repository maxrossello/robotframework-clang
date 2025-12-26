/*
 * Copyright (c) 2025- Massimo Rossello
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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