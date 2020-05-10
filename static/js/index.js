const base64Flag = 'data:image/jpeg;base64,'
const hasAdvancedUpload = 'has-advanced-upload'
const isUploading = 'is-uploading'
const isProcessing = 'is-processing'
const isError = 'is-error'
const isSuccess = 'is-success'
const isDragover = 'is-dragover'

var $userImage = $('#usr_img')
var $processedImage = $('#proc_img')
var $label = $("label[for='file']")
var $left = $('.left')
var $form = $('.input-form')
var $input = $('.input-file')
var $submit = $('.input-button')
var $segmentedOutput = $('.segmented-output')
var $errorMsg = $('.error span')
var $text = $('.text')
var $textOutput = $('.text-output')

var droppedFiles = false
var shouldUseDroppedFile = false

// Check if the user browser has features to enable the 'advanced' drag and drop functionality
var isAdvancedUpload = function () {
    var div = document.createElement('div')
    var isAdvancedUpload = (('draggable' in div) || ('ondragstart' in div && 'ondrop' in div)) && 'FormData' in window && 'FileReader' in window
    if (isAdvancedUpload) console.debug("This browser has advanced upload.")
    return isAdvancedUpload
}()

// Setup the drag and drop file upload logic
if (isAdvancedUpload) {
    $form.addClass(hasAdvancedUpload)
    $segmentedOutput.addClass(hasAdvancedUpload)
    $textOutput.addClass(hasAdvancedUpload)
    $input.hide()

    $form.on('drag dragstart dragend dragover dragenter dragleave drop', function (e) {
        e.preventDefault()
        e.stopPropagation()
    })
        .on('dragover dragenter', function () {
            $form.addClass(isDragover)
            $left.addClass(isDragover)
        })
        .on('dragleave dragend drop', function () {
            $form.removeClass(isDragover)
            $left.removeClass(isDragover)
        })
        .on('drop', function (e) {
            shouldUseDroppedFile = true
            droppedFiles = e.originalEvent.dataTransfer.files
            handleFileFormFilled(droppedFiles[0].name)
        })
} else {
    alert('Please consider switching to a modern browser for this app to function correctly.')
}

// Website intro popup
const popUpString = 
    "Welcome to my OCR web application for comic book pages! " + 
    "<br><br>" +
    "To get started, just upload a comic book page image file in the <b>Upload Pane</b> on the left. " + 
    "<br><br>" +
    "This app works best with traditional comics, specifically those with white speech bubbles in the " + 
    "traditional round shape, but feel free to test any interesting cases you might have and see how the app behaves. " +
    "<br><br>" +
    "Here are some free images provided by Comixology to test with: " + 
    "<br>" +
    "<a href=\"https://imgur.com/a/ORudvOW\">Imgur Link</a>"
addUIPopUp(popUpString)


// This doesn't get called on the drag and drop feature, only when a user clicks the form
$form.on('change', function (e) {
    shouldUseDroppedFile = false
    handleFileFormFilled($form.find('input').val().split("\\").pop())
})

// Called when the user hits the 'upload' button
$form.on('submit', async function (e) {
    e.preventDefault()

    if ($form.hasClass(isUploading)) return false
    if ($segmentedOutput.hasClass(isUploading)) return false
    if ($textOutput.hasClass(isUploading)) return false

    var imageFile = shouldUseDroppedFile ? droppedFiles[0] : $form[0][0].files[0]

    if (!isValidInputImage(imageFile)) {
        return
    }

    $form.addClass(isUploading).removeClass(isError)
    $segmentedOutput.addClass(isUploading).removeClass(isError)
    $textOutput.addClass(isUploading).removeClass(isError)

    $form.addClass(isSuccess)
    displayUserImage(imageFile)

    var formData = new FormData()
    formData.append('image', imageFile)
    await submitSegmentRequest(formData)
    await submitReadRequest(formData)
})

// Used to submit POST request to the /segment api to get a segmented version of the user image
function submitSegmentRequest(formData) {
    return fetch('/segment', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            $form.removeClass(isUploading)
            $segmentedOutput.removeClass(isUploading)
            if (response.status !== 200) {
                $form.addClass(isError)
                $segmentedOutput.addClass(isError)
                $errorMsg.text(response.body)
                return
            }
            response.arrayBuffer().then((buffer) => {
                var imageStr = arrayBufferToBase64(buffer)
                $processedImage.attr("src", base64Flag + imageStr)
                $processedImage.show()
                wrapImageWithLink($processedImage, imageStr)
                $segmentedOutput.removeClass(isUploading)
                $segmentedOutput.addClass(isSuccess)
            })
        })
        .catch(error => {
            console.error(error)
        })
}

// Used to submit POST request to the /read api to get parsed text from the user image
function submitReadRequest(formData) {
    $textOutput.addClass(isProcessing).removeClass(isUploading)

    return fetch('/read', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (response.status !== 200) {
                $textOutput.addClass(isError)
                return
            }
            return response.json()
        })
        .then(data => {
            $textOutput.removeClass(isProcessing)
            $textOutput.addClass(isSuccess)
            for(var i = 0; i < data["pageText"].length; i++) {
                $text.append("<span>"+data["pageText"][i]+"</span><br><br>")
            }
        })
        .catch(error => {
            console.error(error)
        })
}

// Enable the submit button when the file form is filled
function handleFileFormFilled(fileName) {
    showFiles(fileName)
    $submit.prop('disabled', false)
}

// Simple input image validation
function isValidInputImage(image) {
    const imageType = /image.*/

    if (!image) {
        alert('Sorry, please select image to upload')
        return false
    }

    if (!image.type.match(imageType)) {
        alert('Sorry, only images are allowed')
        return false
    }

    if (image.size > (5 * 1000 * 1024)) {
        alert('Sorry, the max allowed size for images is 2MB')
        return false
    }

    return true
}

// Convert array buffer from fetch response into base64
function arrayBufferToBase64(buffer) {
    var binary = ''
    var bytes = [].slice.call(new Uint8Array(buffer))

    bytes.forEach((b) => binary += String.fromCharCode(b))

    return window.btoa(binary)
}

// Display file in the user image img DOM object
function displayUserImage(file) {
    var fr = new FileReader()
    fr.onload = function () {
        $userImage.attr('src', fr.result)
    }
    fr.readAsDataURL(file)
    $userImage.show()
}

// Helper function to handle file name truncation and size limit
function showFiles(fileName) {
    $label.text(truncate(fileName, 10))
}

// Helper function to wrap an image byte string with a link element for that image
function wrapImageWithLink($file, imageStr) {
    $file.wrap($('<a>', {
        href: $file.attr('src'),
        download: "processed_image.jpg"
    }))
}

// Helper function to truncate file names to a given length
function truncate(n, len) {
    var filename = n
    if (n.includes(".")) {
        var ext = n.substring(n.lastIndexOf(".") + 1, n.length).toLowerCase()
        filename = n.replace('.' + ext, '')
    }
    if (filename.length <= len) {
        return n
    }
    filename = filename.substr(0, len) + (n.length > len ? '[...]' : '')
    return n.includes(".") ? filename + '.' + ext : filename
}

function addUIPopUp(s) {
    var $newDiv = $(document.createElement('div'))
    $newDiv.html(s)
    $newDiv.dialog({title: "Welcome!"})
    // Close on click outside of popup
    $('body').click(function(e) {
        if (!$(e.target).closest($newDiv).length){
            $newDiv.dialog('close');
        }
    });
}