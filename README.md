# FastDepth-CoreML

This is a CoreML version of [FastDepth: Fast Monocular Depth Estimation on
Embedded Systems](https://github.com/dwofk/fast-depth). I do not guarantee the
correctness of my conversion.  
The iOS project is based on tucan9389's
[DepthPrediction](https://github.com/tucan9389/DepthPrediction-CoreML), but
with [CoreMLHelpers](https://github.com/hollance/CoreMLHelpers/) for
convenience.

## Installation

Fork this repo because you are going to need to change the certificates so that
you can download this on your own phone. So to make this work for you:

1. Fork this repo and create your own branch and switch to it
1. Create an Apple identifier and login to the Apple Developer website
1. In Xcode, go to Preferences/Accounts and add your Apple ID. If it is just a
   personal one, you should see something like your ID, then the Team should be
   *Your Name* (Personal Team)
1. Then go to the upper left and click on the leftmost icon, the Project
   Navigator button, click on the top left item which is the project
   `FastDepth-CoreML` and then Signing & Capabilities
1. You will see in the Signing section in the Team dropdown, something like
   `Unknown Name (9QJ*M25J77)` click Team and you should see your team.
1. You should now see at the bottom in the Status, "Failed to register the
   Bundle" and that is because you have to create a new identifier which by
   default is com.coremi.fastdepth because you don't own that URL and you can't
   create bundles without owning it. Use Reverse DNS notation of a domain that
   you own to create a valid bundle identifier, for example if you are the
   owner of tongfamily.com then you would type something like
   like `com.tongfamily.fastdepth`. Note that the bundle idenfier is pretty
   picky, so for instance if you have `netdron.es` then it will not accept
   `ex.netdron.fastdepth`, so use .com as that seems to work ok. I'm sure other
   TLD will as well, but if it works, the errors should disappear
1. Now go to Windows/Devices and Simulators and make sure your iPhone is
   plugged into your computer. Simulation as an aside does not work with this
   application, so you need a live phone.
1. Click on Device tab and you should see your device there. You will have to
   wait while the yellow banner on top tells you about what's going on and when
   it is ready. note that if you have Apple Watch tied to your phone, it will
   want to trust set for the device as well. You can ignore this as you not
   using an Apple Watch.
1. Now to to the main screen  and in the icon bar you see a selection of where
   to run it. Click on this and select your phone. Now press play button or go
   to the menu and choose Product > Run and this should compile and load the
   application to your device.
1. The application will now download a certificate and then you need to go to
   Settings > General > VPN & Device Management on your phone and you should
   see in the Developer App section something like "Apple Development: *your
   email*", then click on the right arrow and choose Trust to trust
   applications that come from you.
1. The application should then run with two windows of the real image and then
   the depth map in grey where white means closer to the camera and darker
   means more distance.
1. There is no save facility here, so if you want to save the run, then pull
   down on the Control Center and choose the Record button.

## Example

Recorded on an iPhone X.  
![Demo Video](Assets/demo.gif)
