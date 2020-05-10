# Comic Book Page Reader

## Summary
You can find the deployed app at: http://damishshah.com/comic-book-reader

Python application to identify speech bubbles and read text from comic book pages. This project is mostly being used as a way to collect comic book text data to teach a separate machine learning algorithm to write comic book-esque speech.

## Technologies
Python, Flask, Gunicorn, JavaScript, HTML/CSS, Docker, Docker Compose, Nginx

## Libraries
Pytesseract for OCR (Optical Character Recognition), OpenCV

## Developer Notes

This was an excellent project to deep dive into the above technologies for computer vision with an image subject that I enjoy greatly (comic books).

There are some conveniences when it comes to OCR for comic book pages:
* Comic books tend to be written in all caps limiting the total number of options for characters.
* Speech bubbles are often distinctly shaped and colored from their surrounding to aid with human readability. The fact that they are often round and light colored allows us to leverage OpenCVs built-in contour recognition and helps overall with Pytesseracts OCR.

There are also quite a few challenges:
* Quality can be hit or miss and older comic pages can have plenty of artifacts that can get in the way of either the OCR or the speech bubble recognition. We can mitigate the effects of some of these issues with some intelligent pre-processing of our comic book images.
* Styled text boxes with dark backgrounds are hard to identify for speech bubble recognition with our algorithm and for Pytesseract to read. Stylized text that is extra blocky or written in bubble letters can confused the speech bubble contour recognition.
* Reading order of speech bubbles on certain panels can get complicated and hard to make general rules about. Even with a generous vertical pixel threshold, some bubbles can appear much higher on the page than others, but still be read later in the script flow.

Trade-offs and other considerations:
* Speed vs Accuracy - This application can be VERY SLOW for certain pages. There are occasionally accuracy issues with the OCR for speech bubbles with few words or very small font that can be read as empty speech bubbles. In this case I opted to do multiple passes, shrinking the speech bubble area each time to improve reading accuracy. This does however open us up to expensive edge cases. Certain artistic decisions on a given comic book page can lead to many false positives for identified speech bubble candidates. This tradeoff was acceptable for the purposes of this application. 

## References

Dubray, David & Laubrock, Jochen. (2019). Deep CNN-based Speech Balloon Detection and Segmentation for Comic Books. https://arxiv.org/abs/1902.08137.

I wanted to give a shoutout to the research team from Cornell for their research in this area. I reached out to them when I was considering a Nueral Net approach to this problem and they helped answer some questions that I had. You can read their excellent research paper at the above link and check out their model here: https://github.com/DRDRD18/balloons