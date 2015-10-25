package splash;

import android.app.Activity;
import android.content.res.TypedArray;
import android.os.Bundle;
import android.util.DisplayMetrics;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RelativeLayout;
import android.widget.FrameLayout;
import android.graphics.drawable.Drawable;
import android.app.Activity;
import java.io.InputStream;
import android.util.Log;
import android.view.ViewGroup.LayoutParams;
import android.view.SurfaceHolder;
import android.view.Display;
import android.view.View;
import android.widget.ImageView;
import android.view.animation.ScaleAnimation;
import android.view.animation.AnimationUtils;
import android.view.animation.Animation;
import android.view.animation.Animation.AnimationListener;
import android.view.SurfaceView;
import android.graphics.PixelFormat;
import android.graphics.Point;
import android.content.Context;
import android.view.WindowManager;
import android.view.MotionEvent;
import android.view.View.OnTouchListener;
import android.widget.HorizontalScrollView;
import android.view.animation.AlphaAnimation;
import android.util.AttributeSet;
import android.view.GestureDetector;
import java.util.ArrayList;
import java.util.List;
import android.view.GestureDetector.SimpleOnGestureListener;
import android.view.Gravity;
import android.content.Intent;
import android.net.Uri;
import android.content.SharedPreferences;
import android.content.ServiceConnection;
import android.content.ComponentName;
import android.os.IBinder;

import org.renpy.android.ResourceManager;
import org.renpy.android.SDLSurfaceView;
import splash.InsiderrService;

class SnapHorizontalScrollView extends HorizontalScrollView {
	private static final int SWIPE_MIN_DISTANCE = 5;
	private static final int SWIPE_THRESHOLD_VELOCITY = 300;

	private int mItemsSize = 0;
	private GestureDetector mGestureDetector;
	private int mActiveFeature = 0;

	public SnapHorizontalScrollView(Context context, AttributeSet attrs, int defStyle) {
		super(context, attrs, defStyle);
	}

	public SnapHorizontalScrollView(Context context, AttributeSet attrs) {
		super(context, attrs);
	}

	public SnapHorizontalScrollView(Context context) {
		super(context);
	}

	public void setFeatureItems(int numitems, LinearLayout internalWrapper){
		this.mItemsSize = numitems;
		this.addView(internalWrapper);

 		setOnTouchListener(new View.OnTouchListener() {
 			@Override
 			public boolean onTouch(View v, MotionEvent event) {
 				//If the user swipes
 				if (mGestureDetector.onTouchEvent(event)) {
 					return true;
 				}
 				else if(event.getAction() == MotionEvent.ACTION_UP || event.getAction() == MotionEvent.ACTION_CANCEL ){
 					int scrollX = getScrollX();
 					int featureWidth = v.getMeasuredWidth();
 					mActiveFeature = ((scrollX + (featureWidth/2))/featureWidth);
 					int scrollTo = mActiveFeature*featureWidth;
 					smoothScrollTo(scrollTo, 0);
 					return true;
 				}
 				else{
 					return false;
 				}
 			}
 		});
 		mGestureDetector = new GestureDetector(new MyGestureDetector());
 	}
 	
 	class MyGestureDetector extends SimpleOnGestureListener {
	    @Override
	    public boolean onFling(MotionEvent e1, MotionEvent e2, float velocityX, float velocityY) {
		    try {
			    //right to left
			    if(e1.getX() - e2.getX() > SWIPE_MIN_DISTANCE && Math.abs(velocityX) > SWIPE_THRESHOLD_VELOCITY) {
				    int featureWidth = getMeasuredWidth();
				    mActiveFeature = (mActiveFeature < (mItemsSize - 1))? mActiveFeature + 1:mItemsSize -1;
				    smoothScrollTo(mActiveFeature*featureWidth, 0);
				    return true;
			    }
			    //left to right
			    else if (e2.getX() - e1.getX() > SWIPE_MIN_DISTANCE && Math.abs(velocityX) > SWIPE_THRESHOLD_VELOCITY) {
				    int featureWidth = getMeasuredWidth();
				    mActiveFeature = (mActiveFeature > 0)? mActiveFeature - 1:0;
				    smoothScrollTo(mActiveFeature*featureWidth, 0);
				    return true;
			    }
		    } catch (Exception e) {
		            Log.e("Fling", "There was an error processing the Fling event:" + e.getMessage());
		    }
		    return false;
	    }
    }
}


class CarouselScreenActivity {
    public static LinearLayout mCarouselContainer = null;
    public static SnapHorizontalScrollView mHorizontalScrollView = null;
    
    public static void removeCarousel(){
        if (CarouselScreenActivity.mHorizontalScrollView==null) {
            return;
        }
        // Set animation
        AlphaAnimation anim = new AlphaAnimation(1, 0);
        anim.setDuration(500);
        anim.setAnimationListener(new AnimationListener() {
            @Override
            public void onAnimationStart(Animation animation) {
                Log.d("Python","CarouselScreenActivity Animation started");
            }

            @Override
            public void onAnimationRepeat(Animation animation) {}

            @Override
            public void onAnimationEnd(Animation animation) {
               Log.d("Python","CarouselScreenActivity Animation ended");
               if (CarouselScreenActivity.mHorizontalScrollView!=null) {
                    ((FrameLayout)(CarouselScreenActivity.mHorizontalScrollView.getParent())).removeView(CarouselScreenActivity.mHorizontalScrollView);
                    CarouselScreenActivity.mHorizontalScrollView = null;
                    CarouselScreenActivity.mCarouselContainer = null;
                }
            }
        });
        CarouselScreenActivity.mHorizontalScrollView.startAnimation(anim);
    }
    
    public static void Create(FrameLayout mFrameContainer, Activity activity) {
        Log.d("Python", "CarouselScreenActivity");
        
        // Compute the width of a carousel item based on the screen width and number of initial items.
        final DisplayMetrics displayMetrics = new DisplayMetrics();
        activity.getWindowManager().getDefaultDisplay().getMetrics(displayMetrics);
        final int imageWidth = (int) (displayMetrics.widthPixels);
        final int imageHeight = (int) (displayMetrics.heightPixels);

        // Get the array of puppy resources
        String[] imageFilenames = {"tutorial_0.jpg", "tutorial_1.jpg", "tutorial_2.jpg", "tutorial_3.jpg", "tutorial_4.jpg"};

        // Populate the carousel with items
        ImageView imageItem;
        
        // create the linear layout
        mHorizontalScrollView = new SnapHorizontalScrollView(activity);
        mCarouselContainer = new LinearLayout(activity);
        mCarouselContainer.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT);
        mCarouselContainer.setHorizontalScrollBarEnabled(true);
        mCarouselContainer.setLayoutParams(params);
        mHorizontalScrollView.setLayoutParams(params);
        
        for (int i = 0 ; i < imageFilenames.length ; ++i) {
            // Create new ImageView
            imageItem = new ImageView(activity);

            // Set the shadow background
            //imageItem.setBackgroundResource(R.drawable.shadow);

            // Set the image view resource
            String fileName = imageFilenames[i];
            InputStream is = activity.getClass().getResourceAsStream("/res/" + fileName);
            imageItem.setImageDrawable(Drawable.createFromStream(is, ""));
            int w = imageItem.getDrawable().getIntrinsicWidth();
            int h = imageItem.getDrawable().getIntrinsicHeight();
            float fact = (float)h/(float)w;
            // Set the size of the image view to the previously computed value
            imageItem.setLayoutParams(new LinearLayout.LayoutParams(imageWidth, (int)(imageWidth*fact)));

            /// Add image view to the carousel container
            mCarouselContainer.addView(imageItem);
        }
        
        // add the view here       
        mHorizontalScrollView.setFeatureItems(imageFilenames.length, mCarouselContainer);
        
        mFrameContainer.addView(mHorizontalScrollView);
        mHorizontalScrollView.bringToFront();
    }

}



class ProgressScreen {
    public static RelativeLayout mContainer = null;
    public static ImageView mImageProgress = null;
    
    public static void removeProgressScreen(){
        if (ProgressScreen.mContainer==null) {
            return;
        }
        // Set animation
        AlphaAnimation anim = new AlphaAnimation(1, 0);
        anim.setDuration(500);
        anim.setAnimationListener(new AnimationListener() {
            @Override
            public void onAnimationStart(Animation animation) {
                Log.d("Python","ProgressScreen Animation started");
            }

            @Override
            public void onAnimationRepeat(Animation animation) {}

            @Override
            public void onAnimationEnd(Animation animation) {
               Log.d("Python","ProgressScreen Animation ended");
               if (ProgressScreen.mContainer!=null) {
                    if (ProgressScreen.mImageProgress!=null)
                    {
                        ProgressScreen.mImageProgress.clearAnimation();
                        ProgressScreen.mImageProgress = null;
                    }
                    ((FrameLayout)(ProgressScreen.mContainer.getParent())).removeView(ProgressScreen.mContainer);
                    ProgressScreen.mContainer = null;
                }
            }
        });
        ProgressScreen.mContainer.startAnimation(anim);
    }
    
    public static void Create(FrameLayout mFrameContainer, Activity activity, int aDelay) {
        Log.d("Python", "ProgressScreen");
        
        // Compute the width of a carousel item based on the screen width and number of initial items.
        final DisplayMetrics displayMetrics = new DisplayMetrics();
        activity.getWindowManager().getDefaultDisplay().getMetrics(displayMetrics);
        final int displayWidth = (int) (displayMetrics.widthPixels);
        final int displayHeight = (int) (displayMetrics.heightPixels);

        // create the linear layout
        mContainer = new RelativeLayout(activity);
        RelativeLayout.LayoutParams params = new RelativeLayout.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT);
        mContainer.setHorizontalScrollBarEnabled(true);
        mContainer.setLayoutParams(params);
        mContainer.setBackgroundColor(0xFF212121);
        
        // Set the image view resource
        InputStream is = activity.getClass().getResourceAsStream("/res/welcome.png");
        ImageView imageItem = new ImageView(activity);
        imageItem.setImageDrawable(Drawable.createFromStream(is, ""));
        imageItem.setScaleType(ImageView.ScaleType.CENTER_CROP);
        float fact = (float)imageItem.getDrawable().getIntrinsicHeight()/(float)imageItem.getDrawable().getIntrinsicWidth();
        imageItem.setLayoutParams(new RelativeLayout.LayoutParams(displayWidth, (int)(displayWidth*fact)));
        //imageItem.setLayoutParams(new RelativeLayout.LayoutParams(RelativeLayout.LayoutParams.FILL_PARENT, RelativeLayout.LayoutParams.WRAP_CONTENT));

        /// Add image view to the carousel container
        mContainer.addView(imageItem);

        // Set the image view resource
        InputStream is2 = activity.getClass().getResourceAsStream("/res/progress.png");
        mImageProgress = new ImageView(activity);
        mImageProgress.setImageDrawable(Drawable.createFromStream(is2, ""));
        int w = mImageProgress.getDrawable().getIntrinsicWidth();
        int h = mImageProgress.getDrawable().getIntrinsicHeight();
        RelativeLayout.LayoutParams progressparams = new RelativeLayout.LayoutParams(w,h);
        int maxW = (int)(displayWidth*0.7);
        progressparams.leftMargin = (int)((displayWidth-maxW) / 2);
        progressparams.topMargin = (int)(displayHeight*720/1280);
        mImageProgress.setLayoutParams(progressparams);
        /// Add image view to the carousel container
        mContainer.addView(mImageProgress);        
        
        mFrameContainer.addView(mContainer);
        mContainer.bringToFront();
        
        // Set animation
        ScaleAnimation anim = new ScaleAnimation(1.0f, (float)maxW/(float)w, (float)displayWidth/(float)720, (float)displayWidth/(float)720, Animation.RELATIVE_TO_SELF, 0.0f, Animation.RELATIVE_TO_SELF, 0.0f);
        anim.setDuration(aDelay);
        anim.setFillAfter(true);
        anim.setAnimationListener(new AnimationListener() {
            @Override
            public void onAnimationStart(Animation animation) {
                Log.d("Python","Progress Animation started");
            }

            @Override
            public void onAnimationRepeat(Animation animation) {}

            @Override
            public void onAnimationEnd(Animation animation) {
               Log.d("Python","Progress Animation ended");
               ProgressScreen.mImageProgress = null;
            }
        });
        mImageProgress.startAnimation(anim);
    }

}


public class MyAppActivity extends Activity implements SurfaceHolder.Callback {

    static public Activity myActivity = null;
    static private boolean mShowTutotrial = false;
    private Point mDisplaySize = null;    
    private Intent intentService = null;
    private String lastNotificationMessage = null;

    FrameLayout mFrameLayout;
    ImageView mAnimView = null;
    ImageView imageItem = null;
    FrameLayout mSplashLayout = null;
    boolean skipProgress = false;
    boolean mSurfaceReady = false;
    SurfaceHolder mCameraSurfaceHolder = null;

    public MyAppActivity() {
        super();
        myActivity = this;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WindowManager wm = (WindowManager)getSystemService(Context.WINDOW_SERVICE);
        Display display = wm.getDefaultDisplay();

        mDisplaySize = new Point(display.getWidth(), display.getHeight());
    }

    public void removeTutotrial(){
        if (mSplashLayout != null)
        {
            skipProgress = true;
            mAnimView.clearAnimation();
        }
        //CarouselScreenActivity.removeCarousel();
        ProgressScreen.removeProgressScreen();        
    }

    public void startService(){ 
        Log.d("Python","startService -- doing nothing here");
    }


    /** Defines callbacks for service binding, passed to bindService() */
    boolean mBound = false;
    InsiderrService mInsiderrService = null;
    private ServiceConnection mConnection = new ServiceConnection() {

        @Override
        public void onServiceConnected(ComponentName className, IBinder service) {
            // We've bound to LocalService, cast the IBinder and get LocalService instance
            Log.d("Python","onServiceConnected");
            InsiderrService.LocalBinder binder = (InsiderrService.LocalBinder) service;
            mInsiderrService = binder.getService();
            mBound = true;
        }

        @Override
        public void onServiceDisconnected(ComponentName arg0) {
            Log.d("Python","onServiceDisconnected");
            mInsiderrService = null;
            mBound = false;
        }
    };

    public void startService(String aURL, String aAUTH, String aKEYS, String aSYSTEMURL){
        InsiderrService.BASEURL=aURL;
        InsiderrService.AUTH=aAUTH;
        InsiderrService.KEYS=aKEYS;
        InsiderrService.SYSTEMURL=aSYSTEMURL;
        Log.d( "Python", String.format("BASEURL: %s",  InsiderrService.BASEURL));
        //Log.d( "Python", String.format("AUTH: %s",  InsiderrService.AUTH));
        Log.d( "Python", String.format("KEYS: %s",  InsiderrService.KEYS));
        Log.d( "Python", String.format("SYSTEMURL: %s",  InsiderrService.SYSTEMURL));

        SharedPreferences settings = getSharedPreferences(InsiderrService.PREFS_NAME, Context.MODE_PRIVATE );
        SharedPreferences.Editor editor = settings.edit();
        editor.putString("BASEURL", aURL);
        editor.putString("AUTH", aAUTH);
        editor.putString("KEYS", aKEYS);
        editor.putString("SYSTEMURL", aSYSTEMURL);
        editor.putString("HASH", null);
        editor.commit();

        if (intentService == null) {
            Log.d( "Python", "New service intent");
            intentService = new Intent(this, InsiderrService.class);
        }
        else {
            Log.d( "Python", "Old service intent");
            stopService(intentService);
        }
        
        // now it should read the new values
        startService(intentService);
        //bindService(intentService, mConnection, Context.BIND_AUTO_CREATE);
    }
    
    public void stopService(){
    	if (intentService != null){
        	stopService(intentService);
        	//intentService = null;
        }
    }
    
    public void setShowTutotrial(boolean v){
        this.mShowTutotrial = v;
    }
    protected void onCreateBeforeSurface(ResourceManager mResourceManager) {
        Log.d("Python", "onCreateBeforeSurface()");

        // Create the basic frame layout
        mFrameLayout = new FrameLayout(this);
        mFrameLayout.setBackgroundColor(0xFF212121);
        
        // Load animated image from resource and put it on screen
        mSplashLayout = new FrameLayout(this);
        
        // Load animated image from resource and put it on screen
        mAnimView = new ImageView(this);

        // don't show splash zoom
        //InputStream is = this.getClass().getResourceAsStream("/res/splashlogo.png");
        //mAnimView.setImageDrawable(Drawable.createFromStream(is, ""));

        //int logow = mAnimView.getDrawable().getIntrinsicWidth();
        //int logoh = mAnimView.getDrawable().getIntrinsicHeight();
        //float fact = 0.1f*(float)mDisplaySize.x/720.0f;
        mAnimView.setFocusable(false);
        FrameLayout.LayoutParams animlayoutparams = new FrameLayout.LayoutParams(LayoutParams.WRAP_CONTENT, LayoutParams.WRAP_CONTENT);
        animlayoutparams.gravity = Gravity.CENTER;

        // Load fixed splash screen
        imageItem = new ImageView(this);

        // don't show splash zoom
        //int presplashId = mResourceManager.getIdentifier("presplash", "drawable");
        //imageItem.setImageResource(presplashId);

        imageItem.setFocusable(false);
        FrameLayout.LayoutParams itemlayoutparams = new FrameLayout.LayoutParams(LayoutParams.FILL_PARENT, LayoutParams.WRAP_CONTENT);
        itemlayoutparams.gravity = Gravity.BOTTOM;
        itemlayoutparams.setMargins(0,0,0,mDisplaySize.y/8);        

        // alpha-rgb background - because our image is scaled to height not width 
        mSplashLayout.setBackgroundColor(0xFF212121);
        mAnimView.setLayoutParams(animlayoutparams);
        imageItem.setLayoutParams(itemlayoutparams);
        mSplashLayout.addView(imageItem);
        mSplashLayout.addView(mAnimView);
        mFrameLayout.addView(mSplashLayout);
        mAnimView.setVisibility(View.VISIBLE);
        
        // Set animation
        ScaleAnimation anim = new ScaleAnimation(0.1f, 3.0f, 0.1f, 3.0f, Animation.RELATIVE_TO_SELF, 0.5f, Animation.RELATIVE_TO_SELF, 0.5f);

        // don't show splash zoom
        //anim.setDuration(3000);
        anim.setDuration(1);

        anim.setAnimationListener(new AnimationListener() {
            @Override
            public void onAnimationStart(Animation animation) {
                Log.d("Python","Animation started");
            }

            @Override
            public void onAnimationRepeat(Animation animation) {}

            @Override
            public void onAnimationEnd(Animation animation) {
               Log.d("Python","Animation ended");
               if (!skipProgress) {
                   // don't compensate for not showing splash zoom
                   int aDelayProgress = 2000+3000;
                   if (MyAppActivity.mShowTutotrial) {
                        //CarouselScreenActivity.Create(mFrameLayout, (Activity)MyAppActivity.myActivity);
                        aDelayProgress = 15000+3000;
                   }
                   
                   // create progress frame
                   {
                        Log.d("Python","creating progress");
                        ProgressScreen.Create(mFrameLayout, (Activity)MyAppActivity.myActivity, aDelayProgress);
                        Log.d("Python","progress created");
                   }
               }
               mFrameLayout.removeView(mSplashLayout);
               mAnimView.setImageBitmap(null);
               imageItem.setImageBitmap(null);
               mSplashLayout = null;
            }
        });
        mAnimView.startAnimation(anim);
    }
    
    @Override
    public void setContentView(View aView) {
        //SurfaceView mView
        Log.d("Python", "onCreateAfterSurface()");

        // SDL surface stuff
        //((SDLSurfaceView)aView).setZOrderOnTop(true);
        ((SDLSurfaceView)aView).getHolder().setFormat(PixelFormat.TRANSLUCENT);
        
        mFrameLayout.addView(aView);
        
        if (CarouselScreenActivity.mHorizontalScrollView != null) {
            CarouselScreenActivity.mHorizontalScrollView.bringToFront();
        }
        
        super.setContentView(mFrameLayout);
        mSplashLayout.bringToFront();
    }

    public void surfaceCreated(SurfaceHolder holder) {
        Log.d("Python", "surfaceCreated()");
        mSurfaceReady = true;
    }

    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        Log.d("Python", "surfaceChanged()");
    }

    public void surfaceDestroyed(SurfaceHolder holder) {
        Log.d("Python", "surfaceDestroyed()");
        mSurfaceReady = false;
    }

    public String getLastNotificationMessage(){
        return this.lastNotificationMessage;
    }

    @Override
    protected void onPause() {
        super.onPause();
        Log.d("Python", "pausing");
        this.lastNotificationMessage = "";
    }

    @Override
    protected void onResume() {
        super.onResume();
        Log.d("Python", "resuming");
        String id = getIntent().getStringExtra("NotificationMessage");
        if (id != null) {
            Log.d("Python", String.format("resuming extra intent crap: %s",  id));
            this.lastNotificationMessage = id;
        }
        else {
            Log.d("Python", "resuming NO extra intent");
            this.lastNotificationMessage = "";
        }

    }

    @Override
    protected void onNewIntent(Intent intent)
    {
        super.onNewIntent(intent);
        Log.d("Python", "onNewIntent");
        // set the string passed from the service to the original intent
        setIntent(intent);

    }
}

