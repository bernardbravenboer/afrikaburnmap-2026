package org.afrikaburn.map;
import android.os.Bundle;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Pass null to prevent state restoration which causes rendering issues
        super.onCreate(null);
        WebView.setWebContentsDebuggingEnabled(false);
    }
}
