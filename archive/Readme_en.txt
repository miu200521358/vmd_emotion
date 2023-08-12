----------------------------------------------------------------
----------------------------------------------------------------

　PmxDressup

　　ver1.00.00

　　　　　　　　　　　　　　　　　miu200521358

----------------------------------------------------------------
----------------------------------------------------------------


　Thank you for downloading my work.
　Please check the following before using it.

----------------------------------------------------------------


----------------------------------------------------------------
■ Summary
----------------------------------------------------------------

Tools to generate blinks, eye lines, etc., and conditionally adjust morphs in accordance with motion


----------------------------------------------------------------
Video distribution
----------------------------------------------------------------

(In preparation)

----------------------------------------------------------------
■　Still image for content tree
----------------------------------------------------------------

　VmdEmotion - コンテンツツリー用
　https://seiga.nicovideo.jp/seiga/im11238870

----------------------------------------------------------------
Included files
----------------------------------------------------------------

　PmxDressup_x.xx.xx.exe ... Tool itself (with language-specific batchs)
　Readme.txt ... Readme
　VMD Sizing Wiki ... Link to Wiki
　Content tree still image ... Link to content tree still image
　Body for mesh filling ... Body (made by VRoid)


----------------------------------------------------------------
Operating environment
----------------------------------------------------------------

　Windows 10/11 64bit
　CPU or GPU running OpenGL 4.4 or higher


----------------------------------------------------------------
Startup
----------------------------------------------------------------

Basically, you can start the exe as it is.

The version with logging outputs a log file in the same location as the exe file path.

The file history can be copied by placing "history.json" in the same hierarchy as the exe.


----------------------------------------------------------------
■　Basic Usage
----------------------------------------------------------------

Open the tab for the function you want to execute, load the model and motion, and press the Execute button.
You can see a preview of the entire motion and a close-up of the face.

Eye line generation
　Eye line generation based on head rotation based on motion
　Blink (eyelid movement) is added along with eye line
Blink generation
　Blink generation - Blink is generated according to the motion.
　Blink generation ・Conditions for blink generation and probability of blink generation can be adjusted.
Correction of model breakage
　Morphs that are corrupted by the model can be adjusted to the point where they do not corrupt.
Morph condition adjustment
　Morph values can be adjusted according to interpolation curves.
Motion Integration
　Motion Integration - Integrate multiple motions in both bones and morphs to the extent that they do not all hit.


----------------------------------------------------------------
In case of problems
----------------------------------------------------------------

　The unzipped file is garbled.
　McAfee detects the presence of a virus.
　If you encounter any of these problems, please refer to the following page to see if the problem can be resolved. (This is the FAQ page for VMD Sizing)

　https://github.com/miu200521358/vmd_sizing/wiki/03.-%E5%95%8F%E9%A1%8C%E3%81%8C%E8%B5%B7%E3%81%8D%E3%81%9F%E5%A0%B4%E5%90%88

　If you still cannot solve the problem, please report it in the community.


----------------------------------------------------------------
Community
----------------------------------------------------------------

　Nikoni community: https://com.nicovideo.jp/community/co5387214

　　VMD sizing, motion supporter, and other homebrew tools.
　　You can try out the beta version of the site as soon as possible.
　　I would like to be able to follow up if the tool does not work properly.
　　The site is closed, but it is auto-approved, so please feel free to join!

----------------------------------------------------------------
Terms of use, etc.
----------------------------------------------------------------

　Required Information.

　　If you publish or distribute your motion, please give credit to the motion.
　　If you are a member of Nico Nico Douga, please register the still image (im11209493) for the tree in the contents tree.
　　　If you register your motion in the content tree, the credit is optional.
　　If you are distributing the motion to the general public, please clearly indicate the credit only on the source of the distribution notice (video, etc.) and register it in the content tree.
　　　*It is not necessary to request a credit statement for works that use the motion in question.

　Optional

　　With regard to this tool and motion, you are free to do the following acts within the scope of the terms and conditions of the original motion or model

　　Adjustment or modification of the generated motion
　　　In the case of distributed motions, please confirm that additions and modifications are permitted (not prohibited) by the terms and conditions.
　　Posting videos of models on video-sharing sites, SNS, etc.
　　　Posting of motion and tool captures generated in progress is also acceptable.
　　　However, if the terms of the original motion or model stipulate conditions such as posting destination or age restrictions, the motion generated by this tool will also be subject to those conditions.
　　Distribution of motion to an unspecified number of people
　　　Only for motions that have been created by the user or that have been approved for distribution to an unspecified number of people for additions or modifications.

　Prohibited items

　　Please refrain from the following actions regarding this tool and generated motions

　　Actions outside the scope of the terms and conditions of the original motion, etc.
　　Any comments that are completely self-made.
　　Actions that may cause inconvenience to the rights holders.
　　・Actions that are intended to defame or slander others (regardless of whether they are two-dimensional or three-dimensional).

　　The following conditions are not prohibited, but we ask for your consideration
　　　Use of images that contain excessive violence, obscenity, romantic, bizarre, political, or religious expressions (R-15 or above).

　　　Please be sure to check the scope of the terms and conditions of the original motion picture before using the motion picture.
　　　Please be sure to check the scope of the terms and conditions of the original motion picture before using the motion picture.

　　Please note that "commercial use" is not prohibited in this tool, but is prohibited in PMXEditor.

　Disclaimer

　　- Please use at your own risk.
　　- The author assumes no responsibility for any problems caused by the use of this tool.


----------------------------------------------------------------
Source code library
----------------------------------------------------------------

This tool is written in python, and the following libraries are used and included.

numpy (https://pypi.org/project/numpy/)
bezier (https://pypi.org/project/bezier/)
numpy-quaternion (https://pypi.org/project/numpy-quaternion/)
wxPython (https://pypi.org/project/wxPython/)
pyinstaller (https://pypi.org/project/PyInstaller/)

Source code is available on Github. (MIT License)
However, copyright is not waived.

https://github.com/miu200521358/pmx_dressup

Icons are borrowed from icon-rainbow
https://icon-rainbow.com/%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%81%AE%E7%84%A1%E6%96%99%E3%82%A2%E3%82%A4%E3%82%B3%E3%83 %B3%E7%B4%A0%E6%9D%90-2/

Icons in the tool are borrowed from Google Material Icon.
https://fonts.google.com/icons


----------------------------------------------------------------
Credits
----------------------------------------------------------------

　Tool name: VmdEmotion
　Author: miu or miu200521358

　http://www.nicovideo.jp/user/2776342
　Twitter: @miu200521358
　Mail: garnet200521358@gmail.com


----------------------------------------------------------------
History
----------------------------------------------------------------

