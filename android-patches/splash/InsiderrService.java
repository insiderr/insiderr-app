package splash;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.Binder;
import android.widget.Toast;
import android.util.Log;
import android.os.Looper;
import android.os.Handler;
import android.os.Message;
import android.os.HandlerThread;
import java.lang.Thread;
import android.os.Process;
import android.app.IntentService;
import org.apache.http.client.methods.HttpGet;
import android.net.Uri.Builder;
import android.net.Uri;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.client.HttpClient;
import java.io.BufferedReader;
import org.apache.http.HttpResponse;
import java.io.InputStreamReader;
import android.os.Bundle;
import org.json.JSONObject;
import org.apache.http.util.EntityUtils;
import org.json.JSONArray;
import android.content.Context;
import android.content.SharedPreferences;
import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Activity;
import android.content.ComponentName;
import android.app.Application;
import android.graphics.BitmapFactory;
import android.graphics.Bitmap;
import java.net.URL;
import org.apache.http.HttpHost;
import java.lang.Math;
import java.util.Random;


public class InsiderrService extends IntentService {
  public static final String PREFS_NAME = "InsiderrService";
  public static String BASEURL=null;
  public static String KEYS=null;
  public static String AUTH=null;
  public static String HASH=null;
  public static String SYSTEMURL=null;
  public static String SYSTEMHASH=null;
  public static Boolean mRunning=true;
  public static Boolean mStarting=false;
  private final static String tag = "Python";
  private Looper mServiceLooper;
  private ServiceHandler mServiceHandler;
  private static double[] SleepTimes = {0.25, 0.5, 0.5, 1, 2, 4, 8, 16, 16, 32, 32, 64, 64};
  public static int indexSleepTimes = 0;
  public static HandlerThread threadWorker = null;
  public static Intent serviceIntent = null;

  private final IBinder mBinder = new LocalBinder();

  /**
     * Class used for the client Binder.  Because we know this service always
     * runs in the same process as its clients, we don't need to deal with IPC.
     */
  public class LocalBinder extends Binder {
        InsiderrService getService() {
            Log.d("Python","LocalBinder getService");
            // Return this instance of LocalService so clients can call public methods
            return InsiderrService.this;
        }
  }

  @Override
  public IBinder onBind(Intent intent) {
      Log.d(tag, "onBind");
      //return null;
      return mBinder;
  }


  public void addNotification(String UpdatedKeys, String text){
        int id = getResources().getIdentifier("icon", "drawable", getPackageName());
        Log.d( tag, String.format("ICON ID: %d",  id));
        Notification.Builder mBuilder = new Notification.Builder( getApplicationContext() ).setContentTitle("Insiderr").setContentText(text).setSmallIcon(id);

        Bitmap bmp = BitmapFactory.decodeResource(getResources(), id);
        mBuilder.setLargeIcon(bmp);
        
        // Creates an explicit intent for an Activity in your app
        
        Intent i = new Intent();
        i.setAction(Intent.ACTION_MAIN);
        //i.addCategory(Intent.CATEGORY_LAUNCHER);
        i.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_LAUNCHED_FROM_HISTORY);
        //i.setComponent(new ComponentName( getApplicationContext().getPackageName(), MyAppActivity.class.getName()));
        i.setComponent(new ComponentName( getApplicationContext().getPackageName(), "org.renpy.android.PythonActivity"));
        if (UpdatedKeys != null) {
            i.putExtra("NotificationMessage", UpdatedKeys);
        }
        //Intent resultIntent = new Intent(this, ResultActivity.class);

        int mNotificationId = 001;
        PendingIntent resultPendingIntent =
            PendingIntent.getActivity(
            this.getBaseContext(),
            0,
            i,
            PendingIntent.FLAG_UPDATE_CURRENT
        );

        mBuilder.setContentIntent(resultPendingIntent);
                
        NotificationManager mNotificationManager =
            (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        
        // mId allows you to update the notification later on.
        Notification notifying = mBuilder.getNotification();
        notifying.flags |= Notification.FLAG_AUTO_CANCEL;
        mNotificationManager.notify(mNotificationId, notifying);
      }


  // Handler that receives messages from the thread
  private final class ServiceHandler extends Handler {
      
      HttpClient mHttpClient = null;
      InsiderrService mService = null;
      String mUpdatedKeys = null;

      public ServiceHandler(Looper looper, InsiderrService service) {
          super(looper);
          mService = service;
      }
            
      public int getUpdates(){
        Log.d( tag, "TRYING getUpdates");
        
        SharedPreferences settings = getSharedPreferences(InsiderrService.PREFS_NAME, Context.MODE_PRIVATE );
        if (settings!=null) {
            InsiderrService.BASEURL = settings.getString("BASEURL", InsiderrService.BASEURL);
            InsiderrService.AUTH = settings.getString("AUTH", InsiderrService.AUTH);
            InsiderrService.KEYS = settings.getString("KEYS", InsiderrService.KEYS);
            InsiderrService.SYSTEMURL = settings.getString("SYSTEMURL", InsiderrService.SYSTEMURL);
            InsiderrService.HASH = settings.getString("HASH", InsiderrService.HASH);
        }
        
        Log.d( tag, String.format("BASEURL: %s",  InsiderrService.BASEURL));
        //Log.d( tag, String.format("AUTH: %s",  InsiderrService.AUTH));
        Log.d( tag, String.format("KEYS: %s",  InsiderrService.KEYS));
        Log.d( tag, String.format("SYSTEMURL: %s",  InsiderrService.SYSTEMURL));
        Log.d( tag, String.format("HASH: %s",  InsiderrService.HASH));

        if (mHttpClient==null){
            mHttpClient = new DefaultHttpClient();              
        }
        if (InsiderrService.BASEURL==null || InsiderrService.KEYS==null || InsiderrService.AUTH==null) {
            return 0;
        }
        Builder buildUri = Uri.parse(InsiderrService.BASEURL+InsiderrService.KEYS).buildUpon();
        if ( InsiderrService.HASH!=null ){
            buildUri.appendQueryParameter("hash", InsiderrService.HASH);
        }
        String updateURLstr = buildUri.build().toString();

        URL updateURL = null;
        try {
	        updateURL = new URL( updateURLstr );
	    } catch (Exception e) {
			Log.d( tag, "Update URL parsing failed");
	    	return 0;
        }

        URL systemURL = null;
        String systemURLstr = null;
        if ( InsiderrService.HASH!=null && InsiderrService.SYSTEMURL!=null && InsiderrService.SYSTEMURL.length()>0 ){
            buildUri = Uri.parse(InsiderrService.SYSTEMURL).buildUpon();
            if ( InsiderrService.SYSTEMHASH==null ) {
                InsiderrService.SYSTEMHASH = InsiderrService.HASH;
            }
            buildUri.appendQueryParameter("hash", InsiderrService.SYSTEMHASH);
            systemURLstr = buildUri.build().toString();
            try {
	            systemURL = new URL( systemURLstr );
	        } catch (Exception e) {
			    Log.d( tag, "System URL parsing failed");
            }
        }

        Log.d( tag, String.format("Update url: %s %d %s", updateURL.getHost(), updateURL.getPort(), updateURL.getProtocol() ));
        HttpHost targetHost = new HttpHost(updateURL.getHost(), updateURL.getPort(), updateURL.getProtocol());
        HttpGet get = new HttpGet( updateURLstr );
        Log.d( tag, String.format("InsiderrService url: %s", updateURLstr) );
        get.setHeader("Authorization", InsiderrService.AUTH);
        int numUpdates=0;
        try {
            HttpResponse responseGet = mHttpClient.execute(get);
            int returnCode = 0;
            if ( responseGet.getStatusLine()!=null ) {
                returnCode = responseGet.getStatusLine().getStatusCode();
                Log.d( tag, String.format("InsiderrService get status: %d",  returnCode ) );
            }
            if ( responseGet.getEntity()!=null && returnCode==200 ) {
                String content = EntityUtils.toString( responseGet.getEntity() );
                Log.d( tag, String.format("InsiderrService get: %s",  content ));
                JSONObject responseJson = new JSONObject(content);
                String hash = responseJson.getString("hash");
                String ok = responseJson.getString("ok");
                String updatesStr = responseJson.getString("updates");
                JSONArray updateArray = new JSONArray(updatesStr);
                Log.d( tag, String.format("InsiderrService get: ok %s hash %s updates %d",  ok, hash,updateArray.length() ));
                if ( InsiderrService.HASH!=null ) {
                    numUpdates = updateArray.length();
                    this.mUpdatedKeys = new String("");
                    for (int i=0; i<numUpdates; i++)
                    {
                        try{
                            Log.d( tag, String.format("InsiderrService update: %s",  updateArray.getString(i) ));
                            JSONObject updatePostObject = new JSONObject( updateArray.getString(i) );
                            JSONObject updatePost = new JSONObject( updatePostObject.getString("obj") );
                            String key = updatePost.getString("key");
                            this.mUpdatedKeys = String.format("%s;%s", this.mUpdatedKeys, key);
                        }
                        catch (Exception e) {
                            Log.d( tag, String.format("EXCEPTION -- parsing update"));
                        }
                    }
                    Log.d( tag, String.format("InsiderrService keys: %s",  this.mUpdatedKeys));
                }
                InsiderrService.HASH = hash;
                SharedPreferences.Editor editor = settings.edit();
                editor.putString("HASH", InsiderrService.HASH);
                editor.commit();
            }
            if (systemURL != null) {
                targetHost = new HttpHost(systemURL.getHost(), systemURL.getPort(), systemURL.getProtocol());
                get = new HttpGet( systemURLstr );
                Log.d( tag, String.format("InsiderrService system url: %s", systemURLstr) );
                get.setHeader("Authorization", InsiderrService.AUTH);
                responseGet = mHttpClient.execute(get);
                returnCode = 0;
                if ( responseGet.getStatusLine()!=null ) {
                    returnCode = responseGet.getStatusLine().getStatusCode();
                    Log.d( tag, String.format("InsiderrService system get status: %d",  returnCode ) );
                }
                if ( responseGet.getEntity()!=null && returnCode==200 ) {
                    String content = EntityUtils.toString( responseGet.getEntity() );
                    Log.d( tag, String.format("InsiderrService system get: %s",  content ));
                    JSONObject responseJson = new JSONObject(content);
                    String updatesStr = responseJson.getString("updates");
                    JSONArray updateArray = new JSONArray(updatesStr);
                    if (updateArray.length() > 0) {
                        InsiderrService.SYSTEMHASH = InsiderrService.HASH;
                        if (numUpdates == 0) {
                            numUpdates = updateArray.length() * -1;
                        }
                    }
                }
            }
        }
        catch (Exception e) {
            Log.d( tag, String.format("EXCEPTION -- BASEURL: %s , KEYS: %s",  InsiderrService.BASEURL, InsiderrService.KEYS));
        }
        return numUpdates;
      }

      
      @Override
      public void handleMessage(Message msg) {
          Log.d(tag, "InsiderrService -- starting message");

          // store the thread id, if for some reason it is different than the stored one,
          // we kill ourselves (because someone else started instead of us)
          SharedPreferences settings = getSharedPreferences(InsiderrService.PREFS_NAME, Context.MODE_PRIVATE );
          SharedPreferences.Editor editor = settings.edit();
          editor.putLong("THREADID", Thread.currentThread().getId());
          editor.commit();

          // Normally we would do some work here, like download a file.
          // For our sample, we just sleep for 15 seconds.
          while (InsiderrService.mRunning) {
              synchronized (this) {
                  try {
                      double sleeptime = InsiderrService.SleepTimes[Math.min(InsiderrService.indexSleepTimes, InsiderrService.SleepTimes.length-1)];
                      InsiderrService.indexSleepTimes+=1;

                      Log.d(tag, String.format("Sleeping for: %.2f min", sleeptime));
                      Thread.sleep( (int)(60*1000*sleeptime) );
                      Log.d(tag, "InsiderrService -- wakeup");

                      // check if someone else is in charge
                      long threadid = settings.getLong("THREADID", 0);
                      if ( threadid != Thread.currentThread().getId() ) {
                          Log.d(tag, "InsiderrService -- someone else is in charge -- quitting");
                          break;
                      }

                      int numUpdates = getUpdates();
                      Log.d(tag, String.format("checking updates: %d new updates", numUpdates));
                      
                      // stop service once we have a few updates.
                      // we will be started again once the app is active
                      if ( numUpdates!=0 ) {
                        Log.d(tag, "Stopping service - we got updates");
                        if (mService!=null) {
                            String[] system_note = {
                                "Trending: this post",
                                "This post might be interesting to you",
                                "This post: so hot right now",
                                "This post is on fire",
                                "This post is winning Insiderr today"};
                            String[] post_note = {
                                "Other Insiderrs are commenting...",
                                "New comment...",
                                "This comment might be interesting to you"};

                            String note = post_note[ (new Random()).nextInt(post_note.length) ];
                            if (numUpdates<0)
                            {
                                note = system_note[ (new Random()).nextInt(system_note.length) ];
                            }

                            mService.addNotification( this.mUpdatedKeys, note );
                            this.mUpdatedKeys = null;
                            Log.d(tag, "Stopping service - notified");
                            InsiderrService.indexSleepTimes = 0;
                        }
                        InsiderrService.mRunning = false;
                      }
                  } catch (Exception e) {
                  }
              }
          }
          // Stop the service using the startId, so that we don't stop
          // the service in the middle of handling another job
          stopSelf(msg.arg1);
      }
  }

  public InsiderrService() {
    super("InsiderrService");
    Log.d(tag, "InsiderrService");
  }
  
  @Override
  protected void onHandleIntent(Intent intent) {
        Log.d(tag, "onHandleIntent");

    }
    
    
  @Override
  public void onCreate() {
    // Start up the thread running the service.  Note that we create a
    // separate thread because the service normally runs in the process's
    // main thread, which we don't want to block.  We also make it
    // background priority so CPU-intensive work will not disrupt our UI.
    Log.d(tag, "onCreate");
    InsiderrService.mStarting = true;
    InsiderrService.mRunning = true;
    InsiderrService.threadWorker = new HandlerThread("ServiceStartArguments",
            Process.THREAD_PRIORITY_BACKGROUND);
    InsiderrService.threadWorker.start();

    // Get the HandlerThread's Looper and use it for our Handler
    mServiceLooper = InsiderrService.threadWorker.getLooper();
    mServiceHandler = new ServiceHandler(mServiceLooper, this);
  }

  @Override
  public int onStartCommand(Intent intent, int flags, int startId) {
      Log.d(tag, "onStartCommand");
      //Toast.makeText(this, "service starting", Toast.LENGTH_SHORT).show();

      // For each start request, send a message to start a job and deliver the
      // start ID so we know which request we're stopping when we finish the job
      InsiderrService.indexSleepTimes = 0;
      InsiderrService.serviceIntent = intent;
      if ( InsiderrService.mStarting ) {
        Log.d(tag, "onStartCommand -- message");
          Message msg = mServiceHandler.obtainMessage();
          msg.arg1 = startId;
          mServiceHandler.sendMessage(msg);
      }
      InsiderrService.mStarting = false;


      // If we get killed, after returning from here, restart
      return START_STICKY;
  }

  @Override
  public void onDestroy() {
    Log.d(tag, "onDestroy");
    InsiderrService.mRunning = false;
    if (InsiderrService.serviceIntent != null) {
        stopService(InsiderrService.serviceIntent);
        InsiderrService.serviceIntent = null;
    }
    /*
    if (InsiderrService.threadWorker != null) {
        try {
            InsiderrService.threadWorker.stop();
        }
        catch (Exception e) {
        }
    }*/
    InsiderrService.threadWorker = null;
    //Toast.makeText(this, "service done", Toast.LENGTH_SHORT).show();
  }
}

